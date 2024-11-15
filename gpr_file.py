import numpy as np
import struct
import matplotlib.pyplot as plt
import cv2

class GPR_file:
    def __init__(self, path):
        self.header_read_byte = 40
        self.header_unpack = "I" * 10
        self.other_offset = 512 - 40 + 256 * 4
        self.trace_header_length = 44
        self.trace_header_unpack = "I" * 11
        self.path = path
        self.marker_id = [0]

    def read_file(self):
        with open(self.path, 'rb') as f:
            main_header_block_byte = f.read(self.header_read_byte)
            main_header_block = struct.unpack(self.header_unpack, main_header_block_byte)
            self.NTraces = main_header_block[6]
            self.NSamples = main_header_block[7]
            self.NTextLabels = main_header_block[8]
            self.Tall = main_header_block[9]
            

            GPR_file.skip(f, self.other_offset)
            GPR_file.skip(f, self.NSamples*4)

            self.read_body(f)
            self.marker_id.append(self.NTraces)

    def skip(f, numbers):
        f.read(numbers)

    def read_body(self, f):
        self.image = np.zeros((self.NSamples, self.NTraces))

        for i in range(self.NTraces):
            self.read_trace_header(f, i)
            self.read_trace(f, i)
        

    def read_trace_header(self, f, i):
        trace_header_block_byte = f.read(self.trace_header_length)
        trace_header_block = struct.unpack(self.trace_header_unpack, trace_header_block_byte)
        if trace_header_block[7]:
            self.marker_id.append(i)

    def read_trace(self, f, i):
        trace_body_block_byte = f.read(self.NSamples*4)
        self.image[:, i] = struct.unpack("f"*self.NSamples, trace_body_block_byte)

    def interpolate(self, params):
        number_of_traces = int(params['length_of_wood'] / params['distance_between_trace'])
        chunks = []
        new_markers = []
        for i in range(len(self.marker_id)-1):
            chunks.append(self.image[:,self.marker_id[i]:self.marker_id[i+1]])
        interpolated_image = np.zeros((self.NSamples, number_of_traces))
        number_of_traces_in_chunk = int(number_of_traces / len(chunks))
        new_markers.append(0)
        for num, chunk in enumerate(chunks):
            left = number_of_traces_in_chunk*num
            right = number_of_traces_in_chunk*(num+1)
            new_markers.append(right)
            interpolated_image[:,left:right] = cv2.resize(chunk, ( number_of_traces_in_chunk,self.NSamples),
                                    interpolation=cv2.INTER_CUBIC)
            
        self.image = interpolated_image
        self.NTraces = number_of_traces
        self.marker_id = new_markers


    def plot(self, markers = True):
        plt.imshow(self.image, cmap = 'gray')
        if markers:
            for i in self.marker_id[:-1]:
                plt.plot(np.array([i]*self.NSamples), np.arange(self.NSamples), 'r')
        plt.show()

    def add_geometry(self, sou_x):
        self.iline = np.array([sou_x] * self.NTraces)
        self.xline = np.arange(self.NTraces)

if __name__ == "__main__":
    path = '23_00.gpr'
    asd = GPR_file(path)
    asd.read_file()
    asd.plot()
    import json
    with open('params.json', 'r') as f:
        params = json.load(f)
    asd.interpolate(params['user_params'])
    asd.plot(markers = False)
