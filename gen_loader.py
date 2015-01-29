#!/usr/bin/env python

import os
import os.path
import sys, getopt
import binascii
import struct
import string

class generator(object):
    #
    # struct l_loader_head {
    #      unsigned int	first_instr;
    #      unsigned char	magic[16];	@ BOOTMAGICNUMBER!
    #      unsigned int	l_loader_start;
    #      unsigned int	l_loader_end;
    # };
    file_header = [0, 0, 0, 0, 0, 0, 0]

    #
    # struct entry_head {
    #       unsigned char   magic[8];           @ ENTY
    #       unsigned char   name[8];            @ loader/bl1
    #       unsigned int    start_lba;
    #       unsigned int    count_lba;
    #       unsigned int    flag;               @ boot partition or not
    # };

    entry_name = ['loader', 'bl1']

    block_size = 512

    # set in self.add()
    idx = 0

    # set in self.parse()
    ptable_lba = 0
    stable_lba = 0

    # file pointer
    p_entry = 28
    p_file = 0

    def __init__(self, out_img):
        try:
            self.fp = open(out_img, "wb+")
        except IOError, e:
            print "*** file open error:", e
            sys.exit(3)
        else:
            self.entry_hd = [[0 for col in range(7)] for row in range(5)]

    def __del__(self):
        self.fp.close()

    # parse partition from the primary ptable
    def parse(self, fname):
        try:
            fptable = open(fname, "rb")
        except IOError, e:
            print "*** file open error:", e
            sys.exit(3)
        else:
            # skip the first block in primary partition table
            fptable.read(self.block_size)
            # check whether it's a primary paritition table
            data = struct.unpack("8s", fptable.read(8))
            efi_magic = 'EFI PART'
            if cmp("EFI PART", data[0]):
                print "It's not partition table image."
                sys.exit(4)
            # skip 16 bytes
            fptable.read(16)
            # get lba of both primary partition table and secondary partition table
            data = struct.unpack("QQQQ", fptable.read(32))
            self.ptable_lba = data[0] - 1
            self.stable_lba = data[3] + 1
            # skip 24 bytes
            fptable.read(24)
            data = struct.unpack("i", fptable.read(4))
            pentries = data[0]
            # skip the reset in this block
            fptable.read(self.block_size - 84)

            #for i in range(1, pentries):
                # name is encoded as UTF-16
                #d0,lba,d2,name = struct.unpack("32sQ16s72s", fptable.read(128))
                #plainname = unicode(name, "utf-16")
                #if (not cmp(plainname[0:7], 'l-loader'[0:7])):
                #    print 'bl1_lba: ', lba
                #    self.bl1_lba = lba

            fptable.close()

    def add(self, index, lba, fname):
        try:
            fsize = os.path.getsize(fname)
        except IOError, e:
            print "*** file open error:", e
            sys.exit(4)
        else:
            if (self.idx != index):
                print "wrong entry index: ", index, "expecting ", self.idx
            blocks = (fsize + self.block_size - 1) / self.block_size
            bootp = 1
            # Maybe the file size isn't aligned. So pad it.
            if index == 0:
                if fsize > 2048:
                    print 'loader size exceeds 2KB. file size: ', fsize
                    sys.exit(4)
                else:
                    left_bytes = 2048 - fsize
            elif index == 1:
                left_bytes = fsize % self.block_size
                if left_bytes:
                    left_bytes = self.block_size - left_bytes
            else:
                print "wrong entry index: ", index
                sys.exit(5)
            print 'lba: ', lba, 'blocks: ', blocks, 'bootp: ', bootp, 'fname: ', fname
            # write loader and bl1
            fimg = open(fname, "rb")
            for i in range (0, blocks):
                buf = fimg.read(self.block_size)
                self.fp.seek(self.p_file)
                self.fp.write(buf)
                # p_file is the file pointer of the new binary file
                # At last, it means the total block size of the new binary file
                self.p_file += self.block_size

            if (index == 0):
                self.p_file = 2048
            print 'p_file: ', self.p_file, 'last block is ', fsize % self.block_size, 'bytes', '  tell: ', self.fp.tell(), 'left_bytes: ', left_bytes
            if left_bytes:
                for i in range (0, left_bytes):
                    zero = struct.pack('x')
                    self.fp.write(zero)
                print 'p_file: ', self.p_file, '  pad to: ', self.fp.tell()

            # write entry information at the header
            byte = struct.pack('8s8siii', 'ENTRY', self.entry_name[index], lba, blocks, bootp)
            self.fp.seek(self.p_entry)
            self.fp.write(byte)
            self.p_entry += 28
            self.idx += 1

            fimg.close()

    def hex2(self, data):
        return data > 0 and hex(data) or hex(data & 0xffffffff)

    def end(self):
        self.fp.seek(20)
        start,end = struct.unpack("ii", self.fp.read(8))
        print "start: ", self.hex2(start), 'end: ', self.hex2(end)
        end = start + self.p_file
        print "start: ", self.hex2(start), 'end: ', self.hex2(end)
        self.fp.seek(24)
        byte = struct.pack('i', end)
        self.fp.write(byte)
        self.fp.close()

def main(argv):
    img_loader = 'l-loader'
    img_bl1 = 'bl1.bin'
    img_fip = 'fip.bin'
    img_prm_ptable = 'prm_ptable.img'
    img_sec_ptable = 'sec_ptable.img'
    output_img = 'l-loader.bin'
    try:
        opts, args = getopt.getopt(argv,"ho:",["img_loader=","img_bl1=","img_prm_ptable=","img_sec_ptable="])
    except getopt.GetoptError:
        print 'gen_loader.py -o <l-loader.bin> --img_loader <l-loader> --img_bl1 <bl1.bin> --img_prm_ptable <prm_ptable.img> --img_sec_ptable <sec_ptable.img>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'gen_loader.py -o <l-loader.bin> --img_loader <l-loader> --img_bl1 <bl1.bin> --img_prm_ptable <prm_ptable.img> --img_sec_ptable <sec_ptable.img>'
            sys.exit(1)
        elif opt == '-o':
            output_img = arg
        elif opt in ("--img_loader"):
            img_loader = arg
        elif opt in ("--img_bl1"):
            img_bl1 = arg
        elif opt in ("--img_prm_ptable"):
            img_prm_ptable = arg
        elif opt in ("--img_sec_ptable"):
            img_sec_ptable = arg
    print '+---------------------------------------+'
    print ' Image-loader:     ', img_loader
    print ' Image-bl1:        ', img_bl1
    print ' Image-prm_ptable: ', img_prm_ptable
    print ' Image-sec_ptable: ', img_sec_ptable
    print ' Ouput Image:      ', output_img
    print '+---------------------------------------+\n'

    loader = generator(output_img)
    loader.parse(img_prm_ptable)

    # The first 2KB is reserved
    # The next 2KB is for loader image
    loader.add(0, 4, img_loader)    # img_loader doesn't exist in partition table
    # bl1.bin starts from 4KB
    loader.add(1, 8, img_bl1)      # img_bl1 doesn't exist in partition table

    loader.end()

if __name__ == "__main__":
    main(sys.argv[1:])
