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
    #       unsigned char   name[8];            @ loader/bl1/fip/ptable/stable
    #       unsigned int    start_lba;
    #       unsigned int    count_lba;
    #       unsigned int    flag;               @ boot partition or not
    # };

    entry_name = ['loader', 'bl1', 'fip', 'ptable', 'stable']

    block_size = 512

    # set in self.add()
    idx = 0

    # set in self.parse()
    ptable_lba = 0
    stable_lba = 0
    bios_lba = 0

    # file pointer
    p_entry = 28
    p_file = 0
    file_bytes = 0

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
            data = struct.unpack("QQ", fptable.read(16))
            self.ptable_lba = data[0]
            self.stable_lba = data[1]
            # skip 40 bytes
            fptable.read(40)
            data = struct.unpack("i", fptable.read(4))
            pentries = data[0]
            # skip the reset in this block
            fptable.read(self.block_size - 84)

            for i in range(1, pentries):
                # name is encoded as UTF-16
                d0,lba,d2,name = struct.unpack("32sQ16s72s", fptable.read(128))
                plainname = unicode(name, "utf-16")
                if (not cmp(plainname[0:3], 'bios'[0:3])):
                    bios_lba = lba

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
            if (index == 0) or (index == 1):
                bootp = 1
            elif (index > 0) and (index < 5):
                bootp = 0
            else:
                print "wrong entry index: ", index
                sys.exit(5)
            print 'lba: ', lba, 'blocks: ', blocks, 'bootp: ', bootp
            # write loader and bl1
            fimg = open(fname, "rb")
            for i in range (0, blocks):
                buf = fimg.read(self.block_size)
                self.fp.seek(self.p_file)
                self.fp.write(buf)
                self.p_file += self.block_size
            # It's used to count the file size that could be loaded by OnChipROM
            if (index == 1):
                self.file_bytes = self.p_file
            print 'p_file: ', self.p_file, 'file_bytes: ', self.file_bytes

            # write entry information at the header
            byte = struct.pack('8s8siii', 'ENTRY', self.entry_name[index], lba, blocks, bootp)
            self.fp.seek(self.p_entry)
            self.fp.write(byte)
            self.p_entry += 28
            self.idx += 1

            fimg.close()

    def end(self):
        self.fp.seek(20)
        start,end = struct.unpack("ii", self.fp.read(8))
        print 'start: ', start, 'end: ', end, 'file_bytes: ', self.file_bytes
        end = start + self.file_bytes
        print 'start: ', start, 'end: ', end
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
        opts, args = getopt.getopt(argv,"ho:",["img_loader=","img_bl1=","img_fip=","img_prm_ptable=","img_sec_ptable="])
    except getopt.GetoptError:
        print 'gen_loader.py -o <l-loader.bin> --img_loader <l-loader> --img_bl1 <bl1.bin> --img_fip <fip.bin> --img_prm_ptable <prm_ptable.img> --img_sec_ptable <sec_ptable.img>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'gen_loader.py -o <l-loader.bin> --img_loader <l-loader> --img_bl1 <bl1.bin> --img_fip <fip.bin> --img_prm_ptable <prm_ptable.img> --img_sec_ptable <sec_ptable.img>'
            sys.exit(1)
        elif opt == '-o':
            output_img = arg
        elif opt in ("--img_loader"):
            img_loader = arg
        elif opt in ("--img_bl1"):
            img_bl1 = arg
        elif opt in ("--img_fip"):
            img_fip = arg
        elif opt in ("--img_prm_ptable"):
            img_prm_ptable = arg
        elif opt in ("--img_sec_ptable"):
            img_sec_ptable = arg
    print '+---------------------------------------+'
    print ' Image-loader:     ', img_loader
    print ' Image-bl1:        ', img_bl1
    print ' Image-fip:        ', img_fip
    print ' Image-prm_ptable: ', img_prm_ptable
    print ' Image-sec_ptable: ', img_sec_ptable
    print ' Ouput Image:      ', output_img
    print '+---------------------------------------+\n'

    loader = generator(output_img)
    loader.parse(img_prm_ptable)

    loader.add(0, 0, img_loader)    # img_loader doesn't exist in partition table
    loader.add(1, 12, img_bl1)      # img_bl1 doesn't exist in partition table
    loader.add(2, loader.bios_lba, img_fip)
    loader.add(3, loader.ptable_lba, img_prm_ptable)
    loader.add(4, loader.stable_lba, img_sec_ptable)

    loader.end()

if __name__ == "__main__":
    main(sys.argv[1:])
