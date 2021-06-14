#!/bin/bash

# download FRIM:
# https://forum.doom9.org/showthread.php?t=169651

movie_dir=$1
movie=$2
movie_input="$movie_dir/$movie.mkv"
movie_output="mkv_sbs/${movie}/"

mkdir -p $movie_output

mkvextract tracks ${movie_input} 0:${movie_input}.264

wine /home/vishrut/Downloads/FRIM/x86/FRIMDecode32 -i:mvc ${movie_input}.264 -o - -sbs | ffmpeg -y -f rawvideo -s:v 3840x1080 -r 24000/1001 -i - -c:v libx264 ${movie_output}${movie}.mkv
rm ${movie_input}.264
