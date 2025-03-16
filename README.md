# NFC_TAGV_Decoder
Additional embedded blocks for Gnu Radio which output decoded byte stream to the console. Currently only decoding in one direction (Reader->Tag) is supported. 

This block expects float "1" and "0" for carrier on and carrier off, respectively. Only iso15693 1 in 4 encoding is supported.

To make sure that the block receives correct inputs additional processing is necessary. In the picture below an example of usage of such block with additional processing with Gnu Radio Companion is shown. 

![Screenshot from 2025-03-16 17-23-56](https://github.com/user-attachments/assets/ba6c3c72-47b3-4997-a724-d5474266d3b2)





