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
    PointerProperty,
    IntProperty,
    BoolProperty,
    StringProperty,
    CollectionProperty
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
    #アプライオプション
    mesh_scale : FloatProperty(name="scale",min=0.001,default=1.0)
    bone_scale : FloatProperty(name="scale",min=0.001,default=1.0)

    # bpy.types.Scene.export_selected_mesh_scale = FloatProperty(
    #     name = "スケール",
    #     description = "スケール",
    #     min=0.001,
    #     max=1000.0,
    #     default=1.0)

class KIAIMPORTEXPORT_PT_ui(utils.panel):
    bl_label = "kiaimportexport"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.ui( "mesh" , "kiaimportexport.mesh_export" , "kiaimportexport.mesh_import" , "mesh_scale")
        self.ui( "weight" , "kiaimportexport.weight_export" , "kiaimportexport.weight_import" , False)
        self.ui( "bone" , "kiaimportexport.bone_export" , "kiaimportexport.bone_import", "bone_scale")

    def ui(self , name , oncmd ,offcmd ,scale ):
        props = bpy.context.scene.kiatools_oa        
        box = self.layout.box()
        box.label( text = name )

        row = box.row(align=True)
        row.operator( oncmd , icon = 'COPYDOWN')
        row.operator( offcmd, icon = 'PASTEDOWN')
        if scale != False:
            row.prop(props, scale, icon='BLENDER', toggle=True)


class KIAIMPORTEXPORT_mesh_export(Import_Export):
    """メッシュ情報をエクスポート"""
    bl_idname = "kiaimportexport.mesh_export"
    bl_label = ""
    filename = MODEL_NAME
    def execute(self, context):
        return {'FINISHED'}        

class KIAIMPORTEXPORT_mesh_import(Import_Export):
    """メッシュ情報をインポート"""
    bl_idname = "kiaimportexport.mesh_import"
    bl_label = ""
    filename = MODEL_NAME
    def execute(self, context):
        return {'FINISHED'}        

class KIAIMPORTEXPORT_weight_export(Import_Export):
    """ウェイト情報をエクスポート"""
    bl_idname = "kiaimportexport.weight_export"
    bl_label = ""
    filename = MODEL_NAME
    def execute(self, context):
        return {'FINISHED'}        

class KIAIMPORTEXPORT_weight_import(Import_Export):
    """ウェイト情報をエクスポート"""
    bl_idname = "kiaimportexport.weight_import"
    bl_label = ""
    filename = MODEL_NAME
    def execute(self, context):
        return {'FINISHED'}        

class KIAIMPORTEXPORT_bone_export(Import_Export):
    """ボーン情報をエクスポート"""
    bl_idname = "kiaimportexport.bone_export"
    bl_label = ""
    filename = MODEL_NAME
    def execute(self, context):
        return {'FINISHED'}        

class KIAIMPORTEXPORT_bone_import(Import_Export):
    """ボーン情報をインポート"""
    bl_idname = "kiaimportexport.bone_import"
    bl_label = ""
    filename = MODEL_NAME
    def execute(self, context):
        return {'FINISHED'}        


classes = (
    KIAIMPORTEXPORT_Props_OA,
    KIAIMPORTEXPORT_PT_ui
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.kiaimportexport_props = PointerProperty(type=KIAIMPORTEXPORT_Props_OA)



def unregister():
    
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.kiaimportexport_props

