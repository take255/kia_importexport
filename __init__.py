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
    PointerProperty,
    StringProperty,
    EnumProperty
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
AXIS = (('X','X','X'), ('Y','Y','Y'), ('Z','Z','Z'), ('-X','-X','-X'), ('-Y','-Y','-Y'), ('-Z','-Z','-Z'))
WORLD = (('Blender','Blender','Blender'), ('Maya','Maya','Maya'))

def fullpath(path,filename):
    if path[-1] != '/':
        path += '/'
    return path + filename

def modelname():
    prefs = bpy.context.preferences.addons[__name__].preferences
    return fullpath(prefs.path,prefs.model_name)

def bonename():
    prefs = bpy.context.preferences.addons[__name__].preferences
    return fullpath(prefs.path,prefs.bone_name)

def weightname():
    prefs = bpy.context.preferences.addons[__name__].preferences
    return prefs.path

def animname():
    prefs = bpy.context.preferences.addons[__name__].preferences
    return fullpath(prefs.path,'test.anim')

#---------------------------------------------------------------------------------------
#Props
#---------------------------------------------------------------------------------------
class KIAIMPORTEXPORT_Props_OA(PropertyGroup):
    #option
    upvector : EnumProperty(items = WORLD , name = 'bone upvector',default = 'Blender' ) 

    #FBX option
    scale : FloatProperty(name="scale",min=0.001,default=1.0)
    export_option : EnumProperty(items= (('sel', 'sel', '選択されたもの'),('col', 'col', 'colコレクション')))
    export_mode : EnumProperty(items= (('def', 'def', 'Default'),('ue', 'ue', 'ForUnrealEngine'),('md', 'md', 'ForMarverousDesigner')))
    fbx_path : StringProperty(name = "path")
    axis_forward : EnumProperty(items = AXIS , name = 'forward',default = '-Z' )
    axis_up : EnumProperty(items = AXIS , name = 'up' ,default = 'Y')



#---------------------------------------------------------------------------------------
#UI Preference
#---------------------------------------------------------------------------------------
class KIAIMPORTEXPORT_MT_addonpreferences(AddonPreferences):
    bl_idname = __name__
 
    path : StringProperty(default = PATH)
    model_name : StringProperty(default = MODEL_NAME) 
    bone_name : StringProperty(default = BONE_NAME) 

    def draw(self, context):
        layout = self.layout
        layout.label(text='File Path & File Name')
        col = layout.column()
        col.prop(self, 'path',text = 'path', expand=True)

        row = col.row()
        row.prop(self, 'model_name',text = 'model name', expand=True)
        row.prop(self, 'bone_name',text = 'bone name', expand=True)


#---------------------------------------------------------------------------------------
#UI
#---------------------------------------------------------------------------------------
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
        self.ui( "anim" , "kiaimportexport.anim_export" , "kiaimportexport.anim_import")


        box = col.box()
        box.label(text="WorldSettings")
        box.prop(props, 'upvector', icon='BLENDER' )



        box = col.box()
        box.label(text="FBX")
        
        row = box.row()
        row.operator( 'kiaimportexport.export_format' , text = 'Export FBX' , icon = 'FILE_TICK').mode = 'fbx'
        row.operator( 'kiaimportexport.export_format' , text = 'Export OBJ' , icon = 'FILE_TICK').mode = 'obj'
        
        row = box.row()
        row.prop(props,"export_option", expand=True)
        row.prop(props,"export_mode", expand=True)

        row = box.row()
        row.prop(props,"fbx_path")
        row.operator( 'kiaimportexport.filebrowse' , icon = 'FILE_FOLDER' ,text = "")


        col.prop(props, 'scale', icon='BLENDER', toggle=True)

        row = col.row()
        row.prop(props, 'axis_forward', icon='BLENDER' )
        row.prop(props, 'axis_up', icon='BLENDER')



    def ui(self , name , oncmd ,offcmd ):
        box = self.row.box()
        box.label( text = name )

        row = box.row(align=True)
        row.operator( oncmd , icon = 'FILE_TICK')
        row.operator( offcmd, icon = 'FILEBROWSER')


class KIAIMPORTEXPORT_MT_filebrowse(Operator):
    bl_idname = "kiaimportexport.filebrowse"
    bl_label = "Folder"

    filepath : bpy.props.StringProperty(subtype="FILE_PATH")
    filename : StringProperty()
    directory : StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        #print(self.filepath)
        print((self.filepath, self.filename, self.directory))
        props = bpy.context.scene.kiaimportexport_props        
        props.fbx_path = self.directory
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}



class KIAIMPORTEXPORT_mesh_export(Operator):
    """メッシュ情報をエクスポート"""
    bl_idname = "kiaimportexport.mesh_export"
    bl_label = ""
    def execute(self, context):
        cmd.mesh_export( modelname() )
        return {'FINISHED'}        

class KIAIMPORTEXPORT_mesh_import(Operator):
    """メッシュ情報をインポート"""
    bl_idname = "kiaimportexport.mesh_import"
    bl_label = ""
    def execute(self, context):
        cmd.mesh_import( modelname() )
        return {'FINISHED'}        

class KIAIMPORTEXPORT_weight_export(Operator):
    """ウェイト情報をエクスポート"""
    bl_idname = "kiaimportexport.weight_export"
    bl_label = ""
    def execute(self, context):
        cmd.weight_export(weightname())
        return {'FINISHED'}        

class KIAIMPORTEXPORT_weight_import(Operator):
    """ウェイト情報をインポート"""
    bl_idname = "kiaimportexport.weight_import"
    bl_label = ""
    def execute(self, context):
        cmd.weight_import(weightname())
        return {'FINISHED'}        

class KIAIMPORTEXPORT_bone_export(Operator):
    """ボーン情報をエクスポート"""
    bl_idname = "kiaimportexport.bone_export"
    bl_label = ""
    def execute(self, context):
        cmd.bone_export( bonename() )
        return {'FINISHED'}        

class KIAIMPORTEXPORT_bone_import(Operator):
    """ボーン情報をインポート"""
    bl_idname = "kiaimportexport.bone_import"
    bl_label = ""
    def execute(self, context):
        cmd.bone_import( bonename() )
        return {'FINISHED'}        

class KIAIMPORTEXPORT_anim_export(Operator):
    """アニメーション情報をエクスポート"""
    bl_idname = "kiaimportexport.anim_export"
    bl_label = ""
    def execute(self, context):
        cmd.anim_export(animname())
        return {'FINISHED'}        

class KIAIMPORTEXPORT_anim_import(Operator):
    """アニメーション情報をインポート"""
    bl_idname = "kiaimportexport.anim_import"
    bl_label = ""
    def execute(self, context):
        cmd.anim_import(animname())
        return {'FINISHED'}        


#FBX
class KIAIMPORTEXPORT_export_format(Operator):
    """選択されているモデルのFBX出力"""
    bl_idname = "kiaimportexport.export_format"
    bl_label = ""
    mode : StringProperty(default='fbx') 

    def execute(self, context):
        cmd.export_format(self.mode)
        return {'FINISHED'}        

# #OBJ
# class KIAIMPORTEXPORT_export_obj(Operator):
#     """選択されているモデルのOBJ出力"""
#     bl_idname = "kiaimportexport.export_obj"
#     bl_label = "Export OBJ"
#     def execute(self, context):
#         cmd.export_obj()
#         return {'FINISHED'}        


classes = (
    KIAIMPORTEXPORT_Props_OA,
    KIAIMPORTEXPORT_PT_ui,
    KIAIMPORTEXPORT_MT_addonpreferences,

    KIAIMPORTEXPORT_mesh_export,
    KIAIMPORTEXPORT_mesh_import,
    KIAIMPORTEXPORT_weight_export,
    KIAIMPORTEXPORT_weight_import,
    KIAIMPORTEXPORT_bone_export,
    KIAIMPORTEXPORT_bone_import,
    KIAIMPORTEXPORT_anim_export,
    KIAIMPORTEXPORT_anim_import,


    KIAIMPORTEXPORT_export_format,
    KIAIMPORTEXPORT_MT_filebrowse

)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.kiaimportexport_props = PointerProperty(type=KIAIMPORTEXPORT_Props_OA)



def unregister():
    
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.kiaimportexport_props

