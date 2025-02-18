"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""
# this block receives pulses (only 1 out of 4 encoding, see "iso15693-2" and "iso1569-3" ) of a NTAGV reader (VCD) 
# and decodes them to a stream of bytes which is output to a console
# decoding of tag(VICC) responses will possibly be implemented in a separate block
#


import numpy as np
from enum import Enum
from gnuradio import gr


class NFCV_framer(gr.sync_block):
    class State(Enum):
        DETECT_PREAMBLE = 1
        DETECT_DATA = 2
     
    PREAMBLE_OUT = 5
    EOF_OUT = 6
    # dataframes as they are output by block output in gnu radio
    DATA_0_0_OUT = 1
    DATA_0_1_OUT = 2
    DATA_1_0_OUT = 3
    DATA_1_1_OUT = 4
    CORRUPTED_DATA = 7
        
    SOF_1_in_4 = np.array([0,1,1,1,1,0,1,1], dtype = np.float32)  # starting frame one in four encoding
    EOF = np.array([1,1,0,1], dtype = np.float32)  # end of frame
    DATA_FRAME_0_0 = np.array([1, 0, 1, 1, 1, 1, 1, 1 ], dtype = np.float32) 
    DATA_FRAME_0_1 = np.array([1, 1, 1, 0, 1, 1, 1, 1 ], dtype = np.float32) 
    DATA_FRAME_1_0 = np.array([1, 1, 1, 1, 1, 0, 1, 1 ], dtype = np.float32)  
    DATA_FRAME_1_1 = np.array([1, 1, 1, 1, 1, 1, 1, 0 ], dtype = np.float32) 
    FRAME_LENGTH = 8
    EOF_FRAME_LENGTH = 4
    curr_state = State.DETECT_PREAMBLE  # are we detecting preamble or data?
    nxt_preamble_start_indx = 0 # next index to start searching for preamble
    nxt_data_start_indx = 0
    last_unprocessed_arr = np.array([1, 1, 1, 1,  1, 1, 1 ], dtype = np.float32)   # it should have length of 7 = (dataframe - 1) not 8!
    work_calls = 0

    frame_arr = np.zeros(100, dtype = np.float32)  # array of decoded nfcv frames, same as output
    current_frame_arr_indx = 0 # current index of frame_arr that is written to

    def __init__(self, arg=1.0):  # only default arguments here
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='NFCV_frame_detector',   # will show up in GRC
            in_sig=[np.float32],
            out_sig=[np.float32]
        )
        # if an attribute with the same name as a parameter is found,
        # a callback is registered (properties work, too).
        self.arg = arg
        
    def detectPreamble(self,strtInx, arr):
        if( (arr[strtInx:(strtInx + self.FRAME_LENGTH)] == self.SOF_1_in_4).all() ):  # if sof detected
            return 1
        return 0  # no preamble detected
        
    def detectData(self,strtInx, arr):
    # TBD detect various data frames
        if( (arr[strtInx:(strtInx + self.FRAME_LENGTH)] == self.DATA_FRAME_0_0).all() ):
            #print("byte",":00")
            return  self.DATA_0_0_OUT
        if( (arr[strtInx:(strtInx + self.FRAME_LENGTH)] == self.DATA_FRAME_0_1).all() ):
            #print("byte",":01")
            return  self.DATA_0_1_OUT
        if( (arr[strtInx:(strtInx + self.FRAME_LENGTH)] == self.DATA_FRAME_1_0).all() ):
            #print("byte",":10")
            return  self.DATA_1_0_OUT
        if( (arr[strtInx:(strtInx + self.FRAME_LENGTH)] == self.DATA_FRAME_1_1).all() ):
            #print("byte",":11")
            return  self.DATA_1_1_OUT
        else:
            #print("corrupted byte")
            return 0
        
    def detectEOF(self, strtInx, arr):
        if( (arr[strtInx:(strtInx + self.EOF_FRAME_LENGTH)] == self.EOF ).all() ):  # if eof detected
            return 1
        return 0  # no eof detected
        
    # parse array of 1 to 4 iso15693 dataframes and return the resulting value
    #  ..df1 | df0
    def framearr2hex(self, dfarr):
        result = 0
        indx = 0
        framehex = 0
        for df in dfarr:
            if(df == self.DATA_0_0_OUT):
                framehex = 0 
            if(df == self.DATA_0_1_OUT):
                framehex = 1
            if(df == self.DATA_1_0_OUT):
                framehex = 2
            if(df == self.DATA_1_1_OUT):
                framehex = 3 
            result = result | (framehex << indx)           
            indx = indx + 2  # one frame corresponds to two bits
        return result
        
    # general request format : SOF Flags(1 byte -> 4 frames) Command(1 byte) Parameters Data CRC (2 byte) EOF
    # CRC is shown as is, although CRC and data are transmittd LSB first
    # data payload is shown with LSB bytes being the ones received first
    def decodeFramesToNFCV(self):
        # TBD 1 to 4 encoding is lsb first and least significant byte first
        # decode current_frame_arr_indx
        flag_byte = self.framearr2hex(self.frame_arr[0:4])
        print("-------READER TRANSMISSION START---------")
        print("flag byte is:", hex(flag_byte))
        
        cmd_byte = self.framearr2hex(self.frame_arr[4:8])
        print("cmd byte is:", hex(cmd_byte))
        
        payload = self.framearr2hex(self.frame_arr[8 : self.current_frame_arr_indx - 8 ] )
        print("payload is:", hex(payload))
        
        crc16 = self.framearr2hex( self.frame_arr[ (self.current_frame_arr_indx - 8) : self.current_frame_arr_indx] ) # 8 frames -> 2 bytes 
       # print("crc word is:", hex(crc16))

        #TBD calculated crc is 
        if(self.calcCRC16(  self.framearr2hex( self.frame_arr[0: self.current_frame_arr_indx] ) ) ):
            print("crc is OK:", hex(crc16))
        else: 
            print("crc is NOT OK:", hex(crc16))
        print("-------READER TRANSMISSION END-----------")
        return 0
       
    # the crc is calculated on the whole data starting with the flags
    # returns true if crc is ok, else false
    def calcCRC16(self, data):
        CRC_POLYNOMIAL = 0x8408  # see iso1569-3 for details
        CRC_PRESET = 0xFFFF
        CHECK_VAL = 0xF0B8
        # starting with ls byte of data start calculating crc
        curr_crc = CRC_PRESET
        i = 0 # curr byte of data
        arr_num_of_bytes = 0   # TBD convert size of array of two bits to number of bytes
        if(self.current_frame_arr_indx % 4 == 0):  # if exact number of bytes
            arr_num_of_bytes = self.current_frame_arr_indx / 4
        else:
            arr_num_of_bytes = (self.current_frame_arr_indx // 4) + 1  # else roof division
        
        while(i < arr_num_of_bytes):
            curr_crc = curr_crc ^ ( ( int(data) & ( 0xFF << ( 8 * i ) )  ) >>( 8*i )  )  # xor with current data byte, shift right as well
            for bits in range(8):
                if ((curr_crc & 0x0001) == 0x1):
                    curr_crc = (curr_crc >> 1) ^ CRC_POLYNOMIAL
                else:
                    curr_crc >>= 1
            i+= 1
        return (curr_crc == CHECK_VAL)
    
    # outputs dataframes, eof or preamble 
    def mainParsingLoop(self, input_arr, out_arr):
    # dependent on the current state: look for preamble or detect data frames
        if(self.curr_state == self.State.DETECT_PREAMBLE):  # scan for preamble start 
            if(self.detectPreamble(self.nxt_preamble_start_indx , input_arr)):            
                #print("preamble", self.nxt_preamble_start_indx )
                self.nxt_data_start_indx = self.nxt_preamble_start_indx + self.FRAME_LENGTH
                out_arr[self.nxt_preamble_start_indx] = self.PREAMBLE_OUT # tbd output preamble symbol at self.nxt_preamble_start_indx + self.FRAME_LENGTH - 8 
                self.curr_state = self.State.DETECT_DATA  # go on to detecting dataframes
                return
            else: # no preamble detected, increment search start index
                self.nxt_preamble_start_indx = self.nxt_preamble_start_indx + 1
          
        if(self.curr_state == self.State.DETECT_DATA):
            if(self.detectEOF(self.nxt_data_start_indx , input_arr)):
                #print("eof", self.nxt_data_start_indx)
                self.decodeFramesToNFCV()         # tbd decode the dataframes to real bytes and reset current frame index
                self.current_frame_arr_indx = 0   # reset index
                out_arr[self.nxt_data_start_indx + self.EOF_FRAME_LENGTH  - self.FRAME_LENGTH ] = self.EOF_OUT
                self.nxt_preamble_start_indx = self.nxt_data_start_indx + self.EOF_FRAME_LENGTH
                self.curr_state = self.State.DETECT_PREAMBLE  # go on to detecting preamble
                return
            
            elif (self.detectData(self.nxt_data_start_indx , input_arr) > 0):
                nextData = self.detectData(self.nxt_data_start_indx , input_arr)   # tbd redoing the same calculation is expensive
                out_arr[self.nxt_data_start_indx] = nextData  
                self.frame_arr[self.current_frame_arr_indx] = nextData #  add decoded dataframe to the array at current_frame_arr_indx
                self.nxt_data_start_indx = self.nxt_data_start_indx + self.FRAME_LENGTH
                self.current_frame_arr_indx = self.current_frame_arr_indx + 1 # increment current_frame_arr_indx write index
                return   
             
            else:  # if corrupted byte 
                self.current_frame_arr_indx = 0  #  reset   frame_arr and current_frame_arr_indx
                out_arr[self.nxt_data_start_indx] = self.CORRUPTED_DATA
                self.nxt_preamble_start_indx = self.nxt_data_start_indx + self.EOF_FRAME_LENGTH
                self.curr_state = self.State.DETECT_PREAMBLE  # go on to detecting preamble
                return
        return

    def work(self, input_items, output_items):
        curr_in_with_last_unprocessed_in =  np.concatenate((self.last_unprocessed_arr, input_items[0]), axis = None) # conc current input with last unprocessed array
        stop_indx = len( curr_in_with_last_unprocessed_in) - self.FRAME_LENGTH
        #print(stop_indx)
        while(self.nxt_preamble_start_indx <= stop_indx and self.nxt_data_start_indx <= stop_indx):  # while 
            self.mainParsingLoop( curr_in_with_last_unprocessed_in.view(), output_items[0].view())   # use view instead of copy for efficiency
        self.last_unprocessed_arr =  curr_in_with_last_unprocessed_in[len(curr_in_with_last_unprocessed_in) - self.FRAME_LENGTH + 1:] # update last unprocessed arr for processing during nxt work call 
        max_end_index = max(self.nxt_preamble_start_indx, self.nxt_data_start_indx)
        self.nxt_preamble_start_indx = max_end_index - stop_indx - 1  # convert to index for the next work input
        self.nxt_data_start_indx = max_end_index - stop_indx - 1
        return len(output_items[0])
