import time
import pickle
import bpy
import mathutils as mt
from bge import logic

# Relevant nlu dependencies (https://github.com/GoranM/nlu):
#

# === nlu.geometry ======================================================================

class Mesh:

    def __init__(self, kx_mesh):

        # Public:
        self.scene = logic.getCurrentScene()
        self.kx_mesh = kx_mesh
        self.polygons = [Polygon(kx_mesh.getPolygon(i)) 
                for i in range(kx_mesh.numPolygons)]


class Polygon:
    
    def __init__(self, kx_polygon):

        kx_mesh = kx_polygon.getMesh()

        self.vertices = [kx_mesh.getVertex(0, kx_polygon.getVertexIndex(i)) 
                for i in range(kx_polygon.getNumVertex())]

    # Public:
    @property
    def tex_coords(self):
        return [v.getUV() for v in self.vertices]

    @tex_coords.setter
    def tex_coords(self, coords):
        for v, c in zip(self.vertices, coords):
            v.setUV(c)
    
    @property
    def tex_coords_lists(self):
        return [list(v.getUV()) for v in self.vertices]


# === nlu.time ==========================================================================

class Timer:

    def __init__(self, delta=1):
        
        self.delta = delta
        self.restart()
    
    # Public:
    def done(self):
        
        time_now = time.time()
        if (time_now - self.time_last) > self.delta:
            self.time_last = time_now
            return True

        return False

    def restart(self):
        self.time_last = time.time()


# This module:
#


class ActiveCycle:

    def __init__(self):
        #Public
        self.frames = None
        self.idx = 0
        self.name = ""
        self.direction = 1
        self.overshot = False
        self.at_end = False

    def will_overshoot(self):
        idx_end = len(self.frames) - 1

        if self.idx == idx_end and self.direction == 1:
            return True
        elif self.idx == 0 and self.direction == -1:
            return True

        return False

    # Public
    def next_frame(self):
        frame = self.frames[self.idx]

        self.idx += self.direction

        if self.will_overshoot():
            self.at_end = True

        if self.idx == len(self.frames):
            self.idx = 0
        elif self.idx == -1:
            self.idx = len(self.frames) - 1

        return frame


class TexAnim():

    gobjname_meshes = {}
    
    def __init__(self, gobj,
            cycle_frames=None,
            cycle=None,
            fps=100):

        self.gobj = gobj
        self.gobj_name = self.gobj.name # gone when __del__ called

        self.mesh = self.new_mesh()
        self.gobj_poly = self.mesh.polygons[0]

        if cycle_frames:
            self.cycle_frames = cycle_frames
        else:
            data = eval(self.gobj.controllers[0].script)
            self.cycle_frames = pickle.loads(data)

        cycles = list(self.cycle_frames.keys())
        if not cycle in cycles:
            cycle = cycles[0]

        self.timer = Timer()

        # Public
        self.active_cycle = ActiveCycle()

        self.fps = fps
        self.uv_scale = mt.Matrix.Identity(2)
        self.cycle(cycle)

    def __del__(self):
        self.gobjname_meshes[self.gobj_name].append(self.mesh)

    def new_mesh(self):
        # LibFree crashes sporadically, so this covoluted approach is a necessary evil:

        if self.gobj.name in self.gobjname_meshes:
            meshes = self.gobjname_meshes[self.gobj.name]
        else:
            self.gobjname_meshes[self.gobj.name] = meshes = []

        if meshes:
            mesh = meshes.pop()
            if mesh.scene.invalid:
                meshes.clear()
                mesh = Mesh(logic.LibNew(str(time.time()), "Mesh", [self.gobj.meshes[0].name])[0])
        else:
            mesh = Mesh(logic.LibNew(str(time.time()), "Mesh", [self.gobj.meshes[0].name])[0])

        self.gobj.replaceMesh(mesh.kx_mesh)

        return mesh

    def flip_trans(self, frame):
        fv = [mt.Vector(uv) for uv in frame]
        frame_center = sum(fv, mt.Vector((0, 0)))
        frame_center.magnitude /= len(fv)
        fvo = [uv - frame_center for uv in fv]
        fvot = [self.uv_scale * uv for uv in fvo]
        return [uv + frame_center for uv in fvot]

    # States
    def animation(self):
        if self.timer.done():
            self.show_next_frame()
    
    # Public
    def show_next_frame(self):
        frame = self.active_cycle.next_frame()
        self.gobj_poly.tex_coords = self.flip_trans(frame)

    def cycle(self, cycle_name):
        if cycle_name == self.active_cycle.name:
            return

        self.active_cycle.idx = 0
        self.active_cycle.name = cycle_name
        self.active_cycle.frames = self.cycle_frames[cycle_name]

        self.timer.restart()
        self.show_next_frame()

    #def uv_direction_x(self, d, axis=1):
    #    self.gobj.localScale[axis] = abs(self.gobj.localScale[axis]) * d

    #def uv_direction_y(self, d):
    #    self.uv_direction_x(d, 1)

    @property
    def fps(self):
        return self._fps

    @fps.setter
    def fps(self, fps):
        self.timer.delta = 1/abs(fps) if fps else float("inf")
        self._fps = fps


def make_offset_frame(base_frame, xof, yof):
    return [[x + xof, y + yof] for x, y in base_frame]

def frame_dimensions(frame):
    a = frame[0]
    b = frame[2]
    return abs(a[0] - b[0]), abs(a[1] - b[1])


def get_texanim(gobj):
    if not "sprycle_ta" in gobj:

        if not "animation" in gobj:
            xstep = gobj["xstep"] if "xstep" in gobj and gobj["xstep"] > 0 else 1
            total_frames = gobj["total_frames"] if "total_frames" in gobj and gobj["total_frames"] > 0 else 1

            if total_frames < xstep:
                total_frames = xstep

            base_frame = Mesh(gobj.meshes[0]).polygons[0].tex_coords_lists

            xof, yof = frame_dimensions(base_frame)

            cycle_frames = {"offset": [make_offset_frame(base_frame, xof * (i % xstep), -yof * (i // xstep))
                                        for i in range(total_frames)]}
        else:
            cycle_frames = None

        gobj["sprycle_ta"] = TexAnim(gobj, cycle_frames)

    return gobj["sprycle_ta"]


def all_sensors_positive(cont):
    return sum([s.positive for s in cont.sensors]) == len(cont.sensors)

def a_sensor_positive(cont):
    return sum([s.positive for s in cont.sensors]) > 0

def activate_all_actuators(cont):
    for a in cont.actuators:
        cont.activate(a)


# Public:
def animate(cont):
    if not all_sensors_positive(cont):
        if not "OR" in cont.name or not a_sensor_positive(cont):
            return

    gobj = cont.owner
    ta = get_texanim(gobj)

    if "animation" in gobj:
        ta.cycle(gobj["animation"])

    if "fps" in gobj:
        ta.fps = gobj["fps"]

    if "reversed" in gobj:
        if gobj["reversed"]:
            ta.active_cycle.direction = -1
        else:
            ta.active_cycle.direction = 1
    
    if "xflipped" in gobj:
        if gobj["xflipped"]:
            ta.uv_scale = mt.Matrix.Scale(-1, 2, mt.Vector((1, 0)))
        else:
            ta.uv_scale = mt.Matrix.Identity(2)

    if "yflipped" in gobj:
        if gobj["yflipped"]:
            y_scale = mt.Matrix.Scale(-1, 2, mt.Vector((0, 1)))
        else:
            y_scale = mt.Matrix.Identity(2)
        if "xflipped" in gobj:
            ta.uv_scale = y_scale * ta.uv_scale
        else:
            ta.uv_scale = y_scale

    gobj["current_frame"] = ta.active_cycle.idx

    ta.animation()

    if ta.active_cycle.at_end:
        ta.active_cycle.at_end = False
        activate_all_actuators(cont)

def debug(cont):
    d = {n: len(m) for n, m in TexAnim.gobjname_meshes.items()}
    cont.owner["debug"] = str(len(logic.LibList())) + " | " + str(d)
