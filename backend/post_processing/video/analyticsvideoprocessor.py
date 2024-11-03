import asyncio
import csv
import os
import re
from typing import List, Any, Iterable

import numpy as np

from group_filters.sync_score.sync_score_group_filter import oasis_min_required_data
from post_processing.post_processing_data import PostProcessingData
from post_processing.video.post_processing import VideoPostProcessing
from post_processing.video.video_processor import VideoProcessor


class AnalyticsVideoProcessor(VideoProcessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.participant_data = {}
        self.external_processing_tool = self.setup_external_processing_tool()

    def setup_external_processing_tool(self):
        return VideoPostProcessing()

    async def process(self, batch_size: int = 5):
        await asyncio.sleep(5)
        if self.external_process:
            recording_list = self.prepare_recording_list()
            await self.process_with_external_tool_group_filter(recording_list)
        else:
            await self.process_videos(batch_size)

        if self.group_filters:
            self.aggregate_group_filter_data()

    async def process_with_external_tool_individual_filter(self, recording_list):
        pass

    async def process_with_external_tool_group_filter(self, recording_list: List["PostProcessingData"]):
        existing_process = self.external_processing_tool.check_existing_process()
        if existing_process.get("is_processing"):
            self.logger.warning("Existing process detected. Waiting...")
            while existing_process.get("is_processing"):
                await asyncio.sleep(5)
                existing_process = self.external_processing_tool.check_existing_process()

        self.external_processing_tool.recording_list = recording_list
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.external_processing_tool.execute)

        while True:
            existing_process = self.external_processing_tool.check_existing_process()
            if not existing_process.get("is_processing"):
                break
            await asyncio.sleep(1)

        tasks = []
        for recording_data in recording_list:
            for group_filter in self.group_filters:
                output_csv = os.path.join(self.output_dir, f"{os.path.splitext(recording_data.filename)[0]}.csv")
                tasks.append(self.extract_and_collect_data(group_filter, output_csv, recording_data.participant_id))
        await asyncio.gather(*tasks)

    async def setup_output(self, filename: str, cap):
        participant_id = self.participant_ids_map.get(filename)

        if participant_id:
            if isinstance(participant_id, list):
                for pid in participant_id:
                    self.participant_data[pid] = []
            else:
                self.participant_data[participant_id] = []

    async def handle_frame_output(self, result, participant_id):
        if isinstance(result, np.ndarray):
            return

        elif isinstance(result, list):
            for res in result:
                if participant_id not in self.participant_data:
                    self.participant_data[participant_id] = []
                self.participant_data[participant_id].append(res)

        elif isinstance(result, dict):
            if participant_id not in self.participant_data:
                self.participant_data[participant_id] = []
            self.participant_data[participant_id].append(result)

    def collect_participant_data(self, data):
        participant_id = data.get('participant_id', 'unknown')
        if participant_id not in self.participant_data:
            self.participant_data[participant_id] = []
        self.participant_data[participant_id].append(data)

    async def finalize_output(self):
        tasks = []
        for participant_id, data in self.participant_data.items():
            output_csv = os.path.join(self.output_dir, f"{participant_id}_data.csv")
            tasks.append(self.generate_csv(data, output_csv))
        await asyncio.gather(*tasks)

    def aggregate_group_filter_data(self):
        current_index = {key: 0 for key in self.participant_data}
        while True:
            chunk = {
                key: values[current_index[key]:current_index[key] + oasis_min_required_data]
                for key, values in self.participant_data.items()
            }

            if any(len(data) < oasis_min_required_data for data in chunk.values()):
                break

            data_list = list(chunk.values())

            for group_filter in self.group_filters:
                results = group_filter.aggregate(data_list)

                output_csv_path = os.path.join(self.output_dir, f"{group_filter.name}_aggregated_results.csv")
                with open(output_csv_path, 'a', newline='') as csvfile:
                    csvwriter = csv.writer(csvfile)

                    if isinstance(results, Iterable) and not isinstance(results, (str, bytes)):
                        headers = ['Participant ID', 'Aggregated Result']
                        if csvfile.tell() == 0:  # Write headers only if file is empty
                            csvwriter.writerow(headers)
                        for participant_id, result in zip(self.participant_data.keys(), results):
                            csvwriter.writerow([participant_id, result])
                    else:
                        headers = ['Aggregated Result']
                        if csvfile.tell() == 0:
                            csvwriter.writerow(headers)
                        csvwriter.writerow([results])

            for key in current_index:
                if current_index[key] < len(self.participant_data[key]) - 1:
                    current_index[key] += 1

    async def generate_csv(self, data: List[dict], output_path: str):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._write_csv, data, output_path)

    def _write_csv(self, data: List[dict], output_path: str):
        headers = data[0].keys() if data else []
        with open(output_path, 'w', newline='') as csvfile:
            csvwriter = csv.DictWriter(csvfile, fieldnames=headers)
            csvwriter.writeheader()
            for row in data:
                csvwriter.writerow(row)

    def extract_participant_id(self, filename: str) -> list[Any] | list[str]:
        matches = re.findall(r"(\w+)_.*", filename)
        return matches if matches else ["unknown"]

    async def extract_and_collect_data(self, group_filter, output_csv: str, participant_id: str):
        extracted_data = await group_filter.extract_post_process(output_csv)
        self.participant_data[participant_id] = extracted_data

    def prepare_recording_list(self) -> List["PostProcessingData"]:
        recording_list = []
        for filename in self.video_filenames:
            participant_id = self.extract_participant_id(filename)
            recording_data = PostProcessingData(
                type="video",
                filename=filename,
                session_id=self.session_id,
                participant_id=participant_id,
            )
            recording_list.append(recording_data)
        return recording_list