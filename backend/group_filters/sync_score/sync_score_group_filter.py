from typing import Any, Optional, Union
import numpy as np
import pandas as pd
from av import VideoFrame, AudioFrame
from filters.filter_dict import FilterDict
from group_filters import GroupFilter
from scipy.interpolate import interp1d

from filters.open_face_au.open_face_au_extractor import OpenFaceAUExtractor
from group_filters.sync_score.bow import BoW
from group_filters.sync_score.oasis import oasis

bow_window_size = 8  # how many frames each window contains
bow_word_size = 4  # how many symbols each window is mapped to (window_length / word_length is a prositive integer)
bow_n_bins = (
    3  # the size of the alphabet or the number of symbols used to represent the time series signal
)
bow_strategy = "uniform"  # the strategy used by the Bag-of-Words (BoW) algorithm
oasis_energy_threshold = 0.1  # min signal energy required for the OASIS algorithm
oasis_min_required_data = (
        2 * bow_window_size - 1
)  # min signal length required for the OASIS algorithm

# Warm up the BoW
for _ in range(10):
    BoW(
        window_size=bow_window_size,
        word_size=bow_word_size,
        n_bins=bow_n_bins,
        strategy=bow_strategy,
    ).apply_bow_for_2_participants(
        np.zeros(oasis_min_required_data), np.zeros(oasis_min_required_data)
    )


class SyncScoreGroupFilter(GroupFilter):
    data_len_per_participant = oasis_min_required_data
    num_participants_in_aggregation = 2

    def __init__(self, config: FilterDict, participant_id: str):
        super().__init__(config, participant_id)

        self.au_extractor = OpenFaceAUExtractor()
        self.au_data = {}
    @staticmethod
    def name() -> str:
        return "SYNC_SCORE_GF"

    @staticmethod
    def type() -> str:
        return "SESSION"

    @staticmethod
    def channel() -> str:
        return "video"

    async def process_individual_frame(
            self, original: Optional[Union[VideoFrame, AudioFrame]], ndarray: np.ndarray
    ) -> Any:
        # Extract AU from the frame
        exit_code, _, result = self.au_extractor.extract(ndarray, self.au_data.get("roi", None))
        if exit_code != 0:
            return None

        self.au_data = result

        # Parse AU data and compute smile
        return await self._parse_au_data()

    async def extract_post_process(self, extraction_path: str) -> Any:
        df = pd.read_csv(extraction_path)
        self.au_data['AU06_c'] = df['AU06_c'].tolist()
        self.au_data['AU12_r'] = df['AU12_r'].tolist()

        min_length = min(len(self.au_data['AU06_c']), len(self.au_data['AU12_r']))

        smile_values = []

        for frame_index in range(min_length):
            self.au_data['presence'] = {"AU06": self.au_data['AU06_c'][frame_index]}
            self.au_data['intensity'] = {"AU12": self.au_data['AU12_r'][frame_index]}

            smile_value = await self._parse_au_data()
            if smile_value is not None:
                smile_values.append(smile_value)

        return smile_values

    async def _parse_au_data(self) -> Optional[float]:
        au06_c = self.au_data.get("presence", {}).get("AU06", "-")
        au12_r = self.au_data.get("intensity", {}).get("AU12", "-")

        if au06_c == "-" or au12_r == "-":
            return None

        # Compute smile value
        smile = au12_r if au06_c == 1 else 0
        return smile

    @staticmethod
    def align_data(x: list, y: list, base_timeline: list) -> list:
        interpolator = interp1d(x, y, kind="linear")
        return list(interpolator(base_timeline))

    @staticmethod
    def aggregate(data: list[list[Any]]) -> Any:
        def normalize_data(data: np.ndarray) -> np.ndarray:
            min_val = np.min(data)
            max_val = np.max(data)
            if min_val == max_val:
                if min_val > 0:
                    return data // min_val
                else:
                    return data

            data_normalized = (data - min_val) / (max_val - min_val)

            return data_normalized

        # Normalize data
        normalized_data1 = normalize_data(data[0])
        normalized_data2 = normalize_data(data[1])

        # Apply BoW algorithm on the AU data
        bow = BoW(
            window_size=bow_window_size,
            word_size=bow_word_size,
            n_bins=bow_n_bins,
            strategy=bow_strategy,
        )

        bow1, bow2 = bow.apply_bow_for_2_participants(normalized_data1, normalized_data2)

        # Apply OASIS algorithm for user1->user2 and user2->user1 and take the average
        sync_score_u1u2 = oasis(
            word_user1=bow1[0][0],
            smile_user1=normalized_data1,
            word_bins_user2=bow2,
            smile_user2=normalized_data2,
            window_size=bow_window_size,
            n_bins=bow_n_bins,
            energy_threshold=oasis_energy_threshold,
        )

        sync_score_u2u1 = oasis(
            word_user1=bow2[0][0],
            smile_user1=normalized_data2,
            word_bins_user2=bow1,
            smile_user2=normalized_data1,
            window_size=bow_window_size,
            n_bins=bow_n_bins,
            energy_threshold=oasis_energy_threshold,
        )

        return (sync_score_u1u2 + sync_score_u2u1) / 2.0
