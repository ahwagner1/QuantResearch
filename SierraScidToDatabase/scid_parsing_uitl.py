import os
import json
import numpy as np



class ScidUtility:


    @classmethod
    def parse_scid(cls, file_path: str, offset: int):
        """
        This functions opens the specified scid file and converts it into a numpy array
        It uses a passed offset to determine the location from where to convert the scid files into a numpy array
        If the passed offset is 0 (no load has ever been done for this file), the entire file gets included

        This function returns a np.array of the scid data, and the position of the last record parsed 
        """
        with open(file_path, 'rb') as scid_file:
            scid_file.seek(0, os.SEEK_END)
            file_size = scid_file.tell()
            scid_types = np.dtype([
                ("scdatetime", "<u8"),
                ("open", "<f4"),
                ("high", "<f4"),
                ("low", "<f4"),
                ("close", "<f4"),
                ("numtrades", "<u4"),
                ("totalvolume", "<u4"),
                ("bidvolume", "<u4"),
                ("askvolume", "<u4"),
            ])

            record_size = scid_types.itemsize

            if offset >= file_size:
                offset = file_size - (file_size % record_size)
            elif offset < 56:
                offset = 56
            
            scid_file.seek(offset)
            scid_as_np_array = np.fromfile(scid_file, dtype=scid_types)
            new_position = scid_file.tell()

        return scid_as_np_array, new_position
