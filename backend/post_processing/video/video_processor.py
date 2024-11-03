import asyncio
import os
from abc import ABC, abstractmethod
from typing import Optional, Union, List
import logging

import cv2
import numpy as np


class VideoProcessor(ABC):
    def __init__(
            self,
            session_id: str,
            video_filenames: Union[str, List[str]],
            sessions_path: str,
            output_dir: str,
            filters: Optional[List] = None,
            group_filters: Optional[List] = None,
            external_process: bool = False
    ):
        self.session_id = session_id
        if isinstance(video_filenames, str):
            video_filenames = [video_filenames]
        self.video_filenames = video_filenames
        self.sessions_path = sessions_path
        self.output_dir = output_dir
        self.filters = filters or []
        self.group_filters = group_filters or []
        self.logger = logging.getLogger(__name__)
        self.external_process = external_process
        self.participant_ids_map = {
            filename: self.extract_participant_id(filename) for filename in self.video_filenames
        }

    def extract_participant_id(self, filename: str) -> str:
        return os.path.splitext(filename)[0]

    @abstractmethod
    def setup_external_processing_tool(self):
        pass

    @abstractmethod
    async def process(self, batch_size: int = 5):
        pass

    @abstractmethod
    async def process_with_external_tool_individual_filter(self, **kwargs):
        pass

    @abstractmethod
    async def process_with_external_tool_group_filter(self, **kwargs):
        pass

    @abstractmethod
    async def setup_output(self, **kwargs):
        pass

    @abstractmethod
    async def handle_frame_output(self, results, participant_id: str):
        pass

    @abstractmethod
    def collect_participant_data(self, data, participant_id: str):
        pass

    @abstractmethod
    async def finalize_output(self):
        pass

    async def process_videos(self, batch_size: int = 5):
        tasks = []
        for filename in self.video_filenames:
            input_path = os.path.join(self.sessions_path, self.session_id, filename)
            participant_id = self.participant_ids_map[filename][0]
            tasks.append(self._process_single_video(input_path, filename, batch_size, participant_id))
        await asyncio.gather(*tasks)

    async def _process_single_video(self, input_path: str, filename: str, batch_size: int, participant_id: str):
        loop = asyncio.get_event_loop()
        cap = await loop.run_in_executor(None, cv2.VideoCapture, input_path)
        if not cap.isOpened():
            self.logger.error(f"Cannot open video file: {input_path}")
            raise FileNotFoundError(f"Cannot open video file: {input_path}")

        await self.setup_output(filename, cap)
        batch_frames = []
        global_frame_index = 0

        while True:
            ret, frame = await loop.run_in_executor(None, cap.read)
            if not ret:
                if batch_frames:
                    await self.process_batch(batch_frames, global_frame_index - len(batch_frames), participant_id)
                break

            batch_frames.append(frame)
            if len(batch_frames) == batch_size:
                await self.process_batch(batch_frames, global_frame_index - len(batch_frames), participant_id)
                batch_frames = []

            global_frame_index += 1

        cap.release()
        await self.finalize_output()

    async def process_batch(self, batch_frames: List[np.ndarray], start_frame_index: int, participant_id: str):
        for i, frame in enumerate(batch_frames):
            frame_index = start_frame_index + i
            try:
                results = []
                for filter in self.filters:
                    result = await self.apply_filter(filter, frame, frame_index)
                    if isinstance(result, list):
                        results.extend(result)  # for cases like Manipulation
                    else:
                        results.append(result)  # for cases like Analytics

                if self.group_filters:
                    for group_filter in self.group_filters:
                        result = await self.apply_group_filter(group_filter, frame)
                        self.collect_participant_data(result, participant_id)

                await self.handle_frame_output(result, participant_id)
                await asyncio.sleep(30 / 1000.0)  # Convert ms to seconds
            except Exception as e:
                self.logger.exception(f"Failed to process frame {frame_index}: {e}")

    async def apply_filter(self, filter, frame: np.ndarray, frame_index: int):
        if asyncio.iscoroutinefunction(filter.process):
            return await filter.process(ndarray=frame, frame_index=frame_index)
        else:
            return await asyncio.get_event_loop().run_in_executor(
                None, filter.process, frame, frame_index
            )

    async def apply_group_filter(self, group_filter, frame: np.ndarray):
        if asyncio.iscoroutinefunction(group_filter.process_individual_frame):
            return await group_filter.process_individual_frame(original=None, ndarray=frame)
        else:
            return await asyncio.get_event_loop().run_in_executor(
                None, group_filter.process_individual_frame, None, frame
            )
