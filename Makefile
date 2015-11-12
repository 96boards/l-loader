CROSS_COMPILE=arm-linux-gnueabihf-
CC=$(CROSS_COMPILE)gcc
LD=$(CROSS_COMPILE)ld
OBJCOPY=$(CROSS_COMPILE)objcopy

all: l-loader.bin
l-loader.bin: start.S debug.S
	$(CC) -c -o start.o start.S
	$(CC) -c -o debug.o debug.S
	$(LD) -Bstatic -Tl-loader.lds -Ttext 0xf9800800 start.o debug.o -o loader
	$(OBJCOPY) -O binary loader temp
	python gen_loader.py -o l-loader.bin --img_loader=temp --img_bl1=bl1.bin
	sudo PTABLE=aosp-4G bash -x generate_ptable.sh
	python gen_loader.py -o ptable-aosp-4G.img --img_prm_ptable=prm_ptable.img
	sudo PTABLE=linux-4G bash -x generate_ptable.sh
	python gen_loader.py -o ptable-linux-4G.img --img_prm_ptable=prm_ptable.img
	sudo PTABLE=aosp-8G bash -x generate_ptable.sh
	python gen_loader.py -o ptable-aosp-8G.img --img_prm_ptable=prm_ptable.img
	sudo PTABLE=linux-8G bash -x generate_ptable.sh
	python gen_loader.py -o ptable-linux-8G.img --img_prm_ptable=prm_ptable.img

clean:
	rm -f *.o loader l-loader.bin temp
