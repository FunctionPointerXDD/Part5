#!/bin/bash

ffplay -nodisp -autoexit "$(ls -t ./records/*.wav| head -n1)"
