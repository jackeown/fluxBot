#xhost +local:root # for the lazy and reckless
docker run -it --net=host                       \
	-v /tmp/.X11-unix:/tmp/.X11-unix:rw     \
	-v SSBM.iso:/ROMS/                      \
	-e DISPLAY=$DISPLAY                     \
	-e QT_X11_NO_MITSHM=1                   \
	--shm-size=8G				\
	--privileged				\
	fluxbot
