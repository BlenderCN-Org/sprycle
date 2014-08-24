Sprycle
=======

A sprite animation cycle utility.

<p align="center">
  <img src="https://raw.github.com/GoranM/sprycle/master/explosion.gif" alt="explosion gif"/>
</p>

Cycle playback data can be generated with `sprycle_gen.blend`. By default, this data is stored (in its pickled form) as an internal text within the .blend, ready to be linked in other .blend files, and ultimately consumed by a compatible BGE playback system. The sprycle python module (`sprycle.py`) is one such system, and it is included in this project.

There is also an option to export the data as a json file, which should be more generally useful.

Install
-------

_It is assumed that you already have a modern version of Blender installed (2.71 was used to create this project). If not, you'll need to address that first, of course._

Simply clone the repo with git, or [download the project zip](https://github.com/GoranM/sprycle/archive/master.zip).

You can then open the `sprycle_gen.blend` with Blender, and use the utility.
