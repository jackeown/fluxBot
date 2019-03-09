FROM ubuntu:latest

RUN apt-get update
RUN apt-get install -y \
    git python3 python3-numpy python3-pip \
    build-essential cmake libevdev-dev


# Clean up APT when done.
RUN apt-get clean

WORKDIR /
RUN git clone https://github.com/altf4/dolphin.git

WORKDIR /dolphin
RUN git checkout memorywatcher-rebased
RUN mkdir build

WORKDIR /dolphin/build
RUN cmake ..
RUN make
RUN make install --local
