"""
training.py
-----------
This module provides classes and functions for generating a tensorflow training dataset.
By: Sebastian D. Goodfellow, Ph.D., 2018
"""

# Compatibility imports
from __future__ import absolute_import, division, print_function

# 3rd party imports
import pickle
import numpy as np
import pandas as pd
from ipywidgets import *
import matplotlib.pylab as plt
from sklearn.model_selection import train_test_split


class TrainingDataset(object):

    def __init__(self, waveforms, duration, path, fs, file_name, classes):

        # Set parameters
        self.waveforms = waveforms
        self.duration = duration
        self.path = path
        self.fs = fs
        self.file_name = file_name
        self.classes = classes

        # Set attributes
        self.length = int(self.duration * self.fs)
        self.data = None
        self.data_train = None
        self.data_val = None
        self.labels = None
        self.labels_train = None
        self.labels_val = None

        # Get training dataset
        self._get_dataset()

        # Get training and validation datasets
        self._get_train_val_datasets()

        # Save
        self._save()

    def _get_dataset(self):

        # Create empty DataFrame
        self.data = pd.DataFrame(index=[], columns=range(self.length))
        self.labels = pd.DataFrame(index=[], columns=['file_name', 'label_str', 'label_int'])

        # Loop through waveforms
        for file_name in list(self.waveforms.keys()):

            # Get training segments
            self._get_segments(file_name=file_name)

    def _get_waveform(self, file_name):

        # Get waveform
        waveform = self.waveforms[file_name]

        return (waveform['filtered'], waveform['duration'], waveform['length'], waveform['label_str'],
                waveform['label_int'])

    def _get_segments(self, file_name):

        # Get waveform, duration, length
        waveform, duration, length, label_str, label_int = self._get_waveform(file_name=file_name)

        if any(label_str in label for label in self.classes):

            # Get indices
            indices = self._get_indices(length=length)

            # Slice and append waveform segments
            self._slice(indices=indices, waveform=waveform, file_name=file_name,
                        label_str=label_str, label_int=label_int)

    def _slice(self, indices, waveform, file_name, label_str, label_int):

        # Loop through segments
        for index in indices:

            # Check if segment is complete
            if len(indices[index]) == self.length:

                # Append segment
                self.data.loc[self.data.shape[0]] = waveform[indices[index]].tolist()
                self.labels.loc[self.labels.shape[0]] = [file_name, label_str, label_int]

            # Check if segment is incomplete
            elif len(indices[index]) < self.length:

                # Get padded segment
                waveform_pad = self._zero_pad(waveform=waveform)

                # Append segment
                self.data.loc[self.data.shape[0]] = waveform_pad.tolist()
                self.labels.loc[self.labels.shape[0]] = [file_name, label_str, label_int]

    def _zero_pad(self, waveform):

        # Get remainder
        remainder = self.length - len(waveform)

        return np.pad(waveform, (int(remainder / 2), remainder - int(remainder / 2)), 'constant', constant_values=0)

    def _get_indices(self, length):

        # Count complete segments
        segments, remainder = self._count_segments(length=length)

        # Create complete segment indices
        indices = self._get_complete_indices(segments=segments)

        # Add remainder indices
        indices = self._get_remainder_indices(indices=indices, segments=segments, length=length, remainder=remainder)

        return indices

    def _count_segments(self, length):

        # Count complete sections
        segments = int(np.floor(length / self.length))

        # Count remainder
        remainder = length - self.length * segments

        return segments, remainder

    def _get_complete_indices(self, segments):

        # Create indices dictionary
        indices = dict()

        # Loop through segments
        for segment in range(segments):

            # Get segment
            indices[segment] = np.arange(segment * self.length, (segment + 1) * self.length)

        return indices

    def _get_remainder_indices(self, indices, segments, length, remainder):

        # Check remainder length
        if remainder / self.length >= 0.5 and segments > 0:
            # Get indices
            indices[len(indices)] = np.arange(length - self.length, length)

        elif segments == 0:
            # Get indices
            indices[len(indices)] = np.arange(length)

        return indices

    def plot_interact(self):
        """Launch widget."""
        interact(self.plot, index=(0, self.data.shape[0] - 1, 1))

    def plot(self, index):

        # Get time array
        time = np.arange(self.length) * 1 / self.fs

        # Setup plot
        fig = plt.figure(figsize=(15, 6))
        fig.subplots_adjust(hspace=0.25)
        ax1 = plt.subplot2grid((1, 1), (0, 0))
        ax1.set_title(
            'File Name: ' + self.labels.loc[index, 'file_name'] + '\n'
            'Label: ' + self.labels.loc[index, 'label_str'], fontsize=20
        )

        # Plot waveform
        ax1.plot(time, self.data.loc[index, :], '-k', label='Filtered')
        ax1.set_xlabel('Time, seconds', fontsize=25)
        ax1.set_ylabel('Normalized Amplitude', fontsize=25)
        ax1.set_xlim([0, self.duration])
        ax1.set_ylim([-0.75, 1.5])
        ax1.tick_params(labelsize=18)

        plt.show()

    def _get_train_val_datasets(self):
        """Train/Validation split."""
        self.data_train, self.data_val, self.labels_train, self.labels_val = \
            train_test_split(self.data, self.labels, stratify=self.labels['label_str'], test_size=0.3, random_state=0)

    def _save(self):

        # Create dictionary
        data = dict()
        data['data_train'] = self.data_train
        data['data_val'] = self.data_val
        data['labels_train'] = self.labels_train
        data['labels_val'] = self.labels_val

        # Set path
        path = os.path.join(self.path, 'training')

        # Check for pickle directory
        if not os.path.exists(path):
            os.makedirs(path)

        # Pickle variable
        with open(os.path.join(path, self.file_name), 'wb') as handle:
            pickle.dump(data, handle)
