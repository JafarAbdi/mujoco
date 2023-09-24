import os
from enum import Enum

import mujoco
from mujoco.usd_utilities import *
from pxr import Usd, UsdGeom, UsdLux, UsdShade, Vt, Gf, Sdf
from scipy.spatial.transform import Rotation as R

# TODO: clean this up and remove the if statements
def create_usd_geom_primitive(geom, stage, texture_file):
  geom_type = geom.type
  if geom_type==USDGeomType.Plane.value:
    return USDPlane(geom, stage, texture_file)
  elif geom_type==USDGeomType.Sphere.value:
    return USDSphere(geom, stage, texture_file)
  elif geom_type==USDGeomType.Capsule.value:
    return USDCapsule(geom, stage, texture_file)
  elif geom_type==USDGeomType.Cylinder.value:
    return USDCylinder(geom, stage, texture_file)
  elif geom_type==USDGeomType.Cube.value:
    return USDCube(geom, stage, texture_file)
  elif geom_type==USDGeomType.Cube.value:
    return USDCube(geom, stage, texture_file)

class USDGeomType(Enum):
  """
  Represents different types of geoms we can add to USD
  The values match those found by the enum presented here:
  https://mujoco.readthedocs.io/en/latest/APIreference/APItypes.html#mjtgeom
  """
  Plane = 0
  # Hfield = 1
  Sphere = 2
  Capsule = 3
  # Ellipsoid = 4
  Cylinder = 5
  Cube = 6
  Mesh = 7

class USDGeom(object):
  """
  Parent class for created geoms
  """
  def __init__(self,
               geom=None,
               stage=None,
               texture_file=None):
    self.geom = geom
    self.stage = stage
    self.texture_file = texture_file
    self.type = None
    self.xform = None
    self.prim = None
    self.ref = None

  def set_texture(self):
    if self.texture_file:
      mtl_path = Sdf.Path(f"/World/Looks/Material_{os.path.splitext(os.path.basename(self.texture_file))[0]}")
      mtl = UsdShade.Material.Define(self.stage, mtl_path)
      shader = UsdShade.Shader.Define(self.stage, mtl_path.AppendPath("Shader"))
      shader.CreateIdAttr("UsdPreviewSurface")
      shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set((1.0, 0.0, 0.0))
      shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.5)
      shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)

      diffuse_tx = UsdShade.Shader.Define(self.stage, mtl_path.AppendPath("DiffuseColorTx"))
      diffuse_tx.CreateIdAttr('UsdUVTexture') 

      diffuse_tx.CreateInput('file', Sdf.ValueTypeNames.Asset).Set(self.texture_file)
      diffuse_tx.CreateOutput('rgb', Sdf.ValueTypeNames.Float3)
      shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(diffuse_tx.ConnectableAPI(), 'rgb')
      mtl.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")

      self.prim.GetPrim().ApplyAPI(UsdShade.MaterialBindingAPI)
      UsdShade.MaterialBindingAPI(self.prim).Bind(mtl)
    
  def update_geom(self, new_geom):
    self.update_pos(new_geom.pos)
    self.update_rotation(new_geom.mat)
    self.update_size(new_geom.size)
    self.update_color(new_geom.rgba)
    self.update_transparency(new_geom.rgba[3])
  
  def update_pos(self, new_pos):
    pos = tuple([float(x) for x in new_pos])
    self.xform.AddTranslateOp().Set(pos)

  def update_rotation(self, new_mat):
    r = R.from_matrix(new_mat)
    euler_rotation = r.as_euler('xyz', degrees=True)
    rotation = Gf.Vec3f(float(euler_rotation[0]), float(euler_rotation[1]), float(euler_rotation[2]))
    self.xform.AddRotateXYZOp().Set(rotation)

  # TODO: check to make sure scale and size are the same thing
  def update_size(self, new_size):
    size = tuple([float(x) for x in new_size])
    self.xform.AddScaleOp().Set(value=size)

  def update_color(self, new_color):
    # new_color is the rgba (we extract first three)
    rgba = [(float(x) for x in new_color[:3])]
    self.prim.GetDisplayColorAttr().Set(rgba)

  def update_transparency(self, new_transparency):
    self.prim.GetDisplayOpacityAttr().Set(new_transparency)

  def __str__(self):
    return f'type = {self.type} \ngeom = {self.geom}'
  
class USDPlane(USDGeom):
  """
  Stores information regarding a plane geom in USD
  """

  plane_count = 0

  def __init__(self, 
               geom=None,
               stage=None,
               texture_file=None):
    super().__init__(geom, stage, texture_file)
    self.type = 0
    USDPlane.plane_count += 1
    xform_path = f'/World/Plane_Xform_{USDPlane.plane_count}'
    plane_path = f'{xform_path}/Plane_{USDPlane.plane_count}'
    self.xform = UsdGeom.Xform.Define(stage, xform_path)
    self.prim = UsdGeom.Plane.Define(stage, plane_path)
    self.ref = stage.GetPrimAtPath(plane_path)

    self.set_texture()

  def update_size(self, new_size):
    self.prim.GetAxisAttr().Set("Z")
    self.prim.GetWidthAttr().Set(float(new_size[0]))
    self.prim.GetLengthAttr().Set(float(new_size[1]))

class USDSphere(USDGeom):
  """
  Stores information regarding a sphere geom in USD
  """

  sphere_count = 0

  def __init__(self, 
               geom=None,
               stage=None,
               texture_file=None):
    super().__init__(geom, stage, texture_file)
    self.type = 2
    USDSphere.sphere_count += 1
    xform_path = f'/World/Sphere_Xform_{USDSphere.sphere_count}'
    sphere_path = f'{xform_path}/Sphere_{USDSphere.sphere_count}'
    self.xform = UsdGeom.Xform.Define(stage, xform_path)
    self.prim = UsdGeom.Sphere.Define(stage, sphere_path)
    self.ref = stage.GetPrimAtPath(sphere_path)

    self.set_texture()

class USDCapsule(USDGeom):
  """
  Stores information regarding a capsule geom in USD
  """

  capsule_count = 0

  def __init__(self, 
               geom=None,
               stage=None,
               texture_file=None):
    super().__init__(geom, stage, texture_file)
    self.type = 3
    USDCapsule.capsule_count += 1
    xform_path = f'/World/Capsule_Xform_{USDCapsule.capsule_count}'
    capsule_path = f'{xform_path}/Capsule_{USDCapsule.capsule_count}'
    self.xform = UsdGeom.Xform.Define(stage, xform_path)
    self.prim = UsdGeom.Capsule.Define(stage, sphere_path)
    self.ref = stage.GetPrimAtPath(capsule_path)

    self.set_texture()

class USDCylinder(USDGeom):
  """
  Stores information regarding a capsule geom in USD
  """

  cylinder_count = 0

  def __init__(self, 
               geom=None,
               stage=None,
               texture_file=None):
    super().__init__(geom, stage, texture_file)
    self.type = 5
    USDCylinder.cylinder_count += 1
    xform_path = f'/World/Cylinder_Xform_{USDCylinder.cylinder_count}'
    cylinder_path = f'{xform_path}/Cylinder_{USDCylinder.cylinder_count}'
    self.xform = UsdGeom.Xform.Define(stage, xform_path)
    self.prim = UsdGeom.Cylinder.Define(stage, cylinder_path)
    self.ref = stage.GetPrimAtPath(cylinder_path)

    self.set_texture()

class USDSphere(USDGeom):
  """
  Stores information regarding a sphere geom in USD
  """

  sphere_count = 0

  def __init__(self, 
               geom=None,
               stage=None,
               texture_file=None):
    super().__init__(geom, stage, texture_file)
    self.type = 2
    USDSphere.sphere_count += 1
    xform_path = f'/World/Sphere_Xform_{USDSphere.sphere_count}'
    sphere_path = f'{xform_path}/Sphere_{USDSphere.sphere_count}'
    self.xform = UsdGeom.Xform.Define(stage, xform_path)
    self.prim = UsdGeom.Sphere.Define(stage, sphere_path)
    self.ref = stage.GetPrimAtPath(sphere_path)

    self.set_texture()

class USDCube(USDGeom):
  """
  Stores information regarding a cube geom in USD
  """

  cube_count = 0

  def __init__(self, 
               geom=None,
               stage=None,
               texture_file=None):
    super().__init__(geom, stage, texture_file)
    self.type = 6
    USDCube.cube_count += 1
    xform_path = f'/World/Cube_Xform_{USDCube.cube_count}'
    cube_path = f'{xform_path}/Cube_{USDCube.cube_count}'
    self.xform = UsdGeom.Xform.Define(stage, xform_path)
    self.prim = UsdGeom.Cube.Define(stage, cube_path)
    self.ref = stage.GetPrimAtPath(cube_path)

    self.set_texture()

class USDMesh(USDGeom):
  """
  Stores information regarding a mesh geom in USD
  """

  mesh_count = 0

  def __init__(self,
               mesh_idx,
               geom,
               stage,
               model,
               texture_file):
    super().__init__(geom, stage)

    assert mesh_idx != -1

    mesh_vert_adr_from = model.mesh_vertadr[mesh_idx]
    mesh_vert_adr_to = model.mesh_vertadr[mesh_idx+1] if mesh_idx < model.nmesh - 1 else len(model.mesh_vert)
    mesh_vert = model.mesh_vert[mesh_vert_adr_from:mesh_vert_adr_to]

    mesh_face_adr_from = model.mesh_faceadr[mesh_idx]
    mesh_face_adr_to = model.mesh_faceadr[mesh_idx+1] if mesh_idx < model.nmesh - 1 else len(model.mesh_face)
    mesh_face = model.mesh_face[mesh_face_adr_from:mesh_face_adr_to]

    self.type = 7
    xform_path = f'/World/Mesh_Xform_{USDMesh.mesh_count}'
    mesh_path= f'{xform_path}/Mesh_{USDMesh.mesh_count}'
    self.xform = UsdGeom.Xform.Define(stage, xform_path)
    self.prim = UsdGeom.Mesh.Define(stage, mesh_path)
    self.ref = stage.GetPrimAtPath(mesh_path)

    self.vertices = mesh_vert
    self.prim.GetPointsAttr().Set(self.vertices)

    model.mesh_facenum[mesh_idx]
    self.prim.GetFaceVertexCountsAttr().Set([3 for _ in range(model.mesh_facenum[mesh_idx])])

    self.faces = mesh_face
    self.prim.GetFaceVertexIndicesAttr().Set(self.faces)

    self.texture_file = texture_file
    if texture_file:

      mesh_texcoord_adr_from = model.mesh_texcoordadr[mesh_idx]
      mesh_texcoord_adr_to = model.mesh_texcoordadr[mesh_idx+1] if mesh_idx < model.nmesh - 1 else len(model.mesh_texcoord)
      mesh_texcoord = model.mesh_texcoord[mesh_texcoord_adr_from:mesh_texcoord_adr_to]

      # texid = geom.texid
      # texcoords = model.mesh_texcoord[mesh_texcoord_ranges[texid]:mesh_texcoord_ranges[texid+1]]

      mesh_facetexcoord_ranges = get_facetexcoord_ranges(model.nmesh, model.mesh_facenum)

      facetexcoords = model.mesh_facetexcoord.flatten()
      facetexcoords = facetexcoords[mesh_facetexcoord_ranges[mesh_idx]:mesh_facetexcoord_ranges[mesh_idx+1]]
      self.texcoords = UsdGeom.PrimvarsAPI(self.prim).CreatePrimvar("st",
                                      Sdf.ValueTypeNames.TexCoord2fArray,
                                      UsdGeom.Tokens.faceVarying)

      self.texcoords.Set(mesh_texcoord)
      self.texcoords.SetIndices(Vt.IntArray(facetexcoords.tolist()));

      mtl_path = Sdf.Path(f"/World/Looks/Material_{os.path.splitext(os.path.basename(texture_file))[0]}")
      mtl = UsdShade.Material.Define(stage, mtl_path)
      shader = UsdShade.Shader.Define(stage, mtl_path.AppendPath("Shader"))
      shader.CreateIdAttr("UsdPreviewSurface")
      shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set((1.0, 0.0, 0.0))
      shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.5)
      shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)

      diffuse_tx = UsdShade.Shader.Define(stage,mtl_path.AppendPath("DiffuseColorTx"))
      diffuse_tx.CreateIdAttr('UsdUVTexture') 

      diffuse_tx.CreateInput('file', Sdf.ValueTypeNames.Asset).Set(texture_file)
      diffuse_tx.CreateOutput('rgb', Sdf.ValueTypeNames.Float3)
      shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(diffuse_tx.ConnectableAPI(), 'rgb')
      mtl.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")

      self.prim.GetPrim().ApplyAPI(UsdShade.MaterialBindingAPI)
      UsdShade.MaterialBindingAPI(self.prim).Bind(mtl)

    USDMesh.mesh_count += 1

  def update_geom(self, new_geom):
    self.update_pos(new_geom.pos)
    self.update_rotation(new_geom.mat)
    if not self.texture_file:
      self.update_color(new_geom.rgba)

    # TODO: remove this, temporary
    # self.xform.AddScaleOp().Set(value=(10.0, 10.0, 10.0))
  
class USDLight(object):
  """
  Class for the created lights
  """

  light_count = 0

  def __init__(self,
               stage):
    self.stage = stage
    USDLight.light_count += 1
    xform_path = f'/World/Light_Xform_{USDLight.light_count}'
    light_path = f'{xform_path}/Light_{USDLight.light_count}'
    self.xform = UsdGeom.Xform.Define(stage, xform_path)
    self.prim = UsdLux.SphereLight.Define(stage, light_path)
    self.ref = stage.GetPrimAtPath(light_path)

  def update_light(self, new_light):
    pos = tuple([float(x) for x in new_light.pos])
    self.xform.AddTranslateOp().Set(pos)

    # TODO attributes:
    #   - direction
    #   - intensity
    #   - exposure
    #   - radius
    #   - specular

    self.prim.GetIntensityAttr().Set(15000);


class USDCamera(object):
  """
  Class for created cameras
  """

  camera_count = 0

  def __init__(self,
               stage):
    self.stage = stage
    USDCamera.camera_count += 1
    camera_path = f'/World/Camera_{USDCamera.camera_count}'
    self.prim = UsdGeom.Camera.Define(stage, camera_path)
    self.ref = stage.GetPrimAtPath(camera_path)

  def update_camera(self, new_camera):
    # print("---- Updating camera in USD ----")
    xformAPI = UsdGeom.XformCommonAPI(self.prim)

    # hardcoded values for Robosuite testing and prototype 
    # TODO: use actual camera values
    xformAPI.SetTranslate((2.25, 0.0, 2.1))
    xformAPI.SetRotate((65.0, 0.0, 90.0))
    xformAPI.SetScale((1, 1, 1))

    self.prim.CreateFocalLengthAttr().Set(24)
    self.prim.CreateFocusDistanceAttr().Set(400)





    