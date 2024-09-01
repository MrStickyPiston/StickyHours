CFLAGS=$(shell /usr/bin/python3.12-config --cflags --embed)
LDFLAGS=$(shell /usr/bin/python3.12-config --ldflags --embed)

all: commonfreehours

pyversion.h:
	python3.12 -c "import sys; print(f'#define PY_TAG \"{sys.version_info.major}.{sys.version_info.minor}\"')" > pyversion.h

commonfreehours: main.c pyversion.h
	gcc -o commonfreehours $^ $(CFLAGS) $(LDFLAGS) -fPIE

clean:
	rm -rf ../commonfreehours-0.0.1/usr/bin
	rm -f commonfreehours pyversion.h

install: all
	mkdir -p ../commonfreehours-0.0.1/usr/bin
	cp commonfreehours ../commonfreehours-0.0.1/usr/bin

.PHONY: all clean install
