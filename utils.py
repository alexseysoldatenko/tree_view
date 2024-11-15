import numpy as np
import segyio

def write_all_files_in_folder_to_sgy(gpr_list, save_path):
    fileout = "test_radar.sgy"
    data = []
    all_iline = []
    all_xline = []
    for gpr in gpr_list:
        data.append(gpr.image)
        all_iline.append(gpr.iline)
        all_xline.append(gpr.xline)
        print(gpr.image.shape)
    
    data = np.concatenate(data, axis = 1).T
    all_iline = np.concatenate(all_iline)
    all_xline = np.concatenate(all_xline)
    dtout = 1
    text_header = {1: 'test',2: 'iline: 189, xline: 193',3: ''}
    filenum = 1
    segyio.tools.from_array2D(fileout, data, iline=1, xline=1, format=segyio.SegySampleFormat(1), dt=dtout, delrt=0)
    with segyio.open(fileout, mode='r+') as f:
        f.text[0] = segyio.tools.create_text_header(text_header)
        for itr, x in enumerate(f.header):
            x.update({segyio.TraceField.CDP_X: all_iline[itr]})
            x.update({segyio.TraceField.CDP_Y: all_xline[itr]})