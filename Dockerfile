FROM ubuntu:latest

# use apt-get to install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends apt-utils

# probably add ones from phillip until this works well...
RUN apt-get install -y		\
	git wget unzip		\
	python3			\
	python3-numpy		\
	python3-pip		\
	build-essential		\
	cmake cmake-data	\
	libudev-dev libevdev-dev libevdev2 libevdev-tools \
	libusb-1.0.0-dev 	\
	libao-dev libpulse-dev libxrandr-dev libopenal-dev libasound2-dev \
	libgtk2.0-dev libpng-dev \
	pkg-config		\
	libegl1-mesa-dev mesa-utils mesa-common-dev

RUN apt-get clean
################################


# pip install other dependencies?
#
#
################################




# install dolphin ################
WORKDIR /
RUN git clone https://github.com/altf4/dolphin.git

WORKDIR /dolphin
RUN git checkout memorywatcher-rebased
RUN mkdir build

# weird hack for wxWidgets: ######
RUN ln -s /usr/include/locale.h /usr/include/xlocale.h

WORKDIR /dolphin/build
#RUN cmake -DENABLE_HEADLESS=ON ..
RUN cmake ..
RUN make
#RUN make install --local
RUN make install
##################################


# sets up udev rule for dolphin wii u adapter
RUN mkdir -p /etc/udev/rules.d/
RUN echo 'SUBSYSTEM=="usb", ENV{DEVTYPE}=="usb_device", ATTRS{idVendor}=="057e", ATTRS{idProduct}=="0337", MODE="0666"' > /etc/udev/rules.d/51-gcadapter.rules
RUN udevadm control --reload-rules
##################################

# clone fluxBot ##################
WORKDIR /
RUN git clone https://github.com/jackeown/fluxBot.git

WORKDIR /fluxBot/
##################################
