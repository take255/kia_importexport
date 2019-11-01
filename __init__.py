# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
import bpy
import imp

from bpy.types import( 
    PropertyGroup,
    Panel,
    Operator,
    UIList,
    AddonPreferences
    )

from bpy.props import(
    FloatProperty,
    PointerProperty
    )

from . import utils
from . import cmd

imp.reload(utils)
imp.reload(cmd)


bl_info = {
"name": "kia_importexport",
"author": "kisekiakeshi",
"version": (0, 1),
"blender": (2, 80, 0),
"description": "kia_importexport",
"category": "Object"}

PATH = 'E:/data/blender_ref/pickle/'

MODEL_NAME = 'model.dat'
BONE_NAME = 'bonedata.dat'


class Import_Export(bpy.types.Operator):
    filename = ''

    def __init__(self):
        pass

    def import_pcl(self):
        f = open(  PATH + self.filename  ,'rb')
        imported_models = pickle.load( f )
        f.close()
        return imported_models

    def export_pcl(self,export_data):
        filename = PATH + self.filename
        print(filename)
        f = open( filename, 'wb' )
        pickle.dump( export_data, f ,protocol=2)
        f.close()

        
class KIAIMPORTEXPORT_Props_OA(PropertyGroup):
    scale : FloatProperty(name="scale",min=0.001,default=1.0)


class KIAIMPORTEXPORT_PT_ui(utils.panel):
    bl_label = "kiaimportexport"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        props = bpy.context.scene.kiaimportexport_props        

        col = self.layout.column()
        self.row = col.row()
        self.ui( "mesh" , "kiaimportexport.mesh_export" , "kiaimportexport.mesh_import" )
        self.ui( "weight" , "kiaimportexport.weight_export" , "kiaimportexport.weight_import" )
        self.ui( "bone" , "kiaimportexport.bone_export" , "kiaimportexport.bone_import")

        # if scale != False:
        col.prop(props, 'scale', icon='BLENDER', toggle=True)


    def ui(self , name , oncmd ,offcmd ):
        box = self.row.box()
        box.label( text = name )

        row = box.row(align=True)
        row.operator( offcmd, icon = 'COPYDOWN')
        row.operator( oncmd , icon = 'PASTEDOWN')

        # if scale != False:
        #     row.prop(props, scale, icon='BLENDER', toggle=True)


class KIAIMPORTEXPORT_mesh_export(Import_Export):
    """メッシュ情報をエクスポート"""
    bl_idname = "kiaimportexport.mesh_export"
    bl_label = ""
    def execute(self, context):
        cmd.mesh_export( MODEL_NAME )
        return {'FINISHED'}        

class KIAIMPORTEXPORT_mesh_import(Import_Export):
    """メッシュ情報をインポート"""
    bl_idname = "kiaimportexport.mesh_import"
    bl_label = ""
    def execute(self, context):
        cmd.mesh_import( MODEL_NAME )
        return {'FINISHED'}        

class KIAIMPORTEXPORT_weight_export(Import_Export):
    """ウェイト情報をエクスポート"""
    bl_idname = "kiaimportexport.weight_export"
    bl_label = ""
    def execute(self, context):
        cmd.weight_export()
        return {'FINISHED'}        

class KIAIMPORTEXPORT_weight_import(Import_Export):
    """ウェイト情報をエクスポート"""
    bl_idname = "kiaimportexport.weight_import"
    bl_label = ""
    def execute(self, context):
        cmd.weight_import()
        return {'FINISHED'}        

class KIAIMPORTEXPORT_bone_export(Import_Export):
    """ボーン情報をエクスポート"""
    bl_idname = "kiaimportexport.bone_export"
    bl_label = ""
    def execute(self, context):
        cmd.bone_export( BONE_NAME )
        return {'FINISHED'}        

class KIAIMPORTEXPORT_bone_import(Import_Export):
    """ボーン情報をインポート"""
    bl_idname = "kiaimportexport.bone_import"
    bl_label = ""
    def execute(self, context):
        cmd.bone_import( BONE_NAME )
        return {'FINISHED'}        


classes = (
    KIAIMPORTEXPORT_Props_OA,
    KIAIMPORTEXPORT_PT_ui,

    KIAIMPORTEXPORT_mesh_export,
    KIAIMPORTEXPORT_mesh_import,
    KIAIMPORTEXPORT_weight_export,
    KIAIMPORTEXPORT_weight_import,
    KIAIMPORTEXPORT_bone_export,
    KIAIMPORTEXPORT_bone_import

)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.kiaimportexport_props = PointerProperty(type=KIAIMPORTEXPORT_Props_OA)



def unregister():
    
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.kiaimportexport_props

