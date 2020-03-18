import numpy as np
import bpy
import bmesh
from bpy.props import FloatProperty

from mathutils import (Vector , Matrix)
import pickle
import imp
import math

from . import utils
imp.reload(utils)


#---------------------------------------------------------------------------------------
#pickle
#---------------------------------------------------------------------------------------
def import_pcl(filename):
    f = open(  filename  ,'rb')
    dat = pickle.load( f )
    f.close()
    return dat

def export_pcl(filename , export_data):
    f = open( filename, 'wb' )
    pickle.dump( export_data, f ,protocol=0)
    f.close()


#---------------------------------------------------------------------------------------
#mesh format
#---------------------------------------------------------------------------------------
class MeshFormat:
    name = ''
    vtxCount = 0
    polygonCount = 0
    def __init__(self,obj):
        props = bpy.context.scene.kiaimportexport_props 

        if obj != []:
            self.name = obj.name
            m = Matrix(obj.matrix_world).to_3x3()
    
            self.m_rot = []
            for i in range(3):
                self.m_rot.append( [x for x in m[i]] )


            loc = [x for x in obj.location ]
            if props.upvector == 'Maya':
                self.location = [loc[0] , loc[2] , -loc[1]] 

            elif props.upvector == 'Blender':
                self.location = loc

        
        self.points = [] #頂点の配列 [ index , [ x ,y , z ] ]
        self.faces = [] #ポリゴンの配列　[ index, vertexarray[] , uarray[] , varray[] ] 
        self.hardedge = []
        self.sharpedge = []
        
    
    def export(self):
        return [ [ self.name , self.vtxCount , self.polygonCount , self.m_rot ,self.location ] , self.points , self.faces ,  self.hardedge ,self.sharpedge]

    def getData(self,dataArray ,scale ):

        self.name = dataArray[0][0]
        self.vtxCount = dataArray[0][1]
        self.polygonCount = dataArray[0][2]
        self.m_rot = Matrix(dataArray[0][3]).to_4x4()
        self.location = Vector(dataArray[0][4])

        self.points = dataArray[1]
        self.faces = dataArray[2]

        #頂点の配列
        self.vtxarray = [ [ x[1][0]*scale , x[1][1]*scale , x[1][2]*scale] for x in self.points]

        #頂点インデックス、U　、V　の配列を一列に並べる
        self.polyarray = []
        self.uarray = []
        self.varray = []

        for face in self.faces:

            self.polyarray.append(face[1])
            self.uarray.append(face[2])
            self.varray.append(face[3])


#---------------------------------------------------------------------------------------
#vertex format
#---------------------------------------------------------------------------------------
class Vtx:
    """頂点出力のためのクラス"""
    co = ''
    
    class Weight:
        """ウェイトの構造体"""
        value = 0
        name = ''

    def __init__(self):
        self.weight = []

    def getWeight(self,index,weight,boneArray):
        w = self.Weight()
        w.value = weight
        w.name =  boneArray[index]
        self.weight.append(w)

    def normalize_weight(self):
        sum = 0
        for w in self.weight:
            sum += w.value

        for w in self.weight:
            #w.value = str(w.value/sum)
            w.value = w.value/sum

    def export(self):
        return [[w.name , w.value] for w in self.weight]

#---------------------------------------------------------------------------------------
#polygon format
#---------------------------------------------------------------------------------------
class Polygon:
    """ポリゴン出力のためのクラス"""
    def __init__(self):
        pass

#---------------------------------------------------------------------------------------
#bone format
#---------------------------------------------------------------------------------------
class Bone:
    name = ''
    parent = None
    head = [0.0,0.0,0.0]
    tail = [1.0,0.0,0.0]
    flg_connect = False #ジョイントをコネクトするかどうかのフラグ。

    def __init__(self,bone):
        self.name = bone[0]

        self.matrix = bone[1]
        self.vector = bone[2]

        self.parent = bone[3]

        self.childlen = []
        for c in bone[4]:
            self.childlen.append(c)


        self.head = self.matrix[12:15]
        self.tail = Vector(self.head) + Vector(self.vector)


    def SetHead(self,val):
        x = np.array(val.split(' ')[:-1])#配列の最後が''になるので削除
        self.head = x.astype(np.float)

    def SetTail(self,val):
        x = np.array(val.split(' ')[:-1])
        self.tail = x.astype(np.float)

    def SetMatrix(self,val):
        x = np.array(val.split(' ')[:-1])
        vec = x.astype(np.float)
        self.matrix = mathutils.Matrix([vec[0:4],vec[4:8],vec[8:12],vec[12:16]])


    def draw(self,amt , dic):
        self.bone = amt.data.edit_bones.new(self.name)
        self.bone.head = self.head

        #tailを割り出す
        # vectorと子供の内積が1ならばその子供の位置をtailにする
        #対象の子供があった場合、その子供のジョイントのコネクトフラグをＯＮにする
        if self.childlen != []:
            self.bone.tail = dic[self.childlen[0]].head
            dic[self.childlen[0]].flg_connect = True
        else:
            self.bone.tail = self.tail.xyz

    def DoParent(self,dic):
        if self.parent != None:
            if self.parent in dic:
                self.bone.parent = dic[self.parent].bone
            if self.flg_connect == True:
                self.bone.use_connect = True



#---------------------------------------------------------------------------------------
#mesh export
#---------------------------------------------------------------------------------------
def mesh_export(filename):
    props = bpy.context.scene.kiaimportexport_props 

    meshArray = []
    for obj in utils.selected():
        #objname = obj.name
        
        msh = obj.data        
        vertices = obj.data.vertices
        polygons = obj.data.polygons

        bm = bmesh.new()
        bm.from_mesh(msh)

        #頂点の情報
        vtxCount = str(len(vertices))#頂点数
        vtxArray = []

        if props.upvector == 'Maya':
            #vector = (v[0],v[2],v[1])
            for v in vertices:
                vtx = Vtx()
                vtxArray.append(vtx)
                vtx.co = Vector([ v.co[0] , v.co[2] , -v.co[1] ]) * props.scale

        elif props.upvector == 'Blender':
            #vector = (v[0],v[1],v[2])
            for v in vertices:
                vtx = Vtx()
                vtxArray.append(vtx)
                vtx.co = v.co * props.scale


        # for v in vertices:
        #     vtx = Vtx()
        #     vtxArray.append(vtx)
        #     vtx.co = v.co * props.scale

        #ポリゴンの情報
        polygonCount = str(len(polygons))#頂点数
        polygonArray = []
        UVarray = []
        for face in polygons:
            polygonArray.append(face.vertices)
        
            #UVの情報
            u_data = []
            v_data = []
            for loop_idx in face.loop_indices:
                uv_coords = obj.data.uv_layers.active.data[loop_idx].uv
                u_data.append(uv_coords.x)
                v_data.append(uv_coords.y)
            UVarray.append([u_data,v_data])


        meshformat = MeshFormat(obj)
        meshArray.append(meshformat)


        # Edge information
        # Detect hard edge
        #print(obj.data.use_auto_smooth)
        #print(obj.data.auto_smooth_angle)
        if obj.data.use_auto_smooth:
            #obj.data.auto_smooth_angle = 1.39626
            rad = obj.data.auto_smooth_angle
            #meshformat.hardedge = [f.index for e in bm.edges if e.calc_face_angle() > rad for f in e.link_faces ]
            #meshformat.hardedge = [f.index for e,e1 in zip(bm.edges,obj.data.edges) if e.calc_face_angle() > rad or e1.use_edge_sharp == True for f in e.link_faces ]

            for e,e1 in zip(bm.edges , obj.data.edges):
                faces = e.link_faces
                angle = 0
                if len(faces) == 2:
                    angle = e.calc_face_angle()
                    if angle > rad or e1.use_edge_sharp == True:
                        meshformat.hardedge.append([f.index for f in faces])
        #meshformat.sharpedge = [e for e in obj.data.edges if e.use_edge_sharp]
        # edgearray = []
        # for e in bm.edges:
        #     angle = math.degrees(e.calc_face_angle())
        #     edgearray.append([angle,[f.index for f in e.link_faces]])

        # meshformat.hardedge = [x[1] for x in edgearray if x[0] > 80 ]




        #オブジェクト名とマトリックス
        #meshformat.name = objname
        #meshformat.setmatrix(Matrix(obj.matrix_world))

        #頂点情報----------------------------------------
        meshformat.vtxCount = vtxCount

        for i,vtx in enumerate(vtxArray):
            meshformat.points.append( [ i , [x for x in vtx.co] ])

        #フェース情報----------------------------------------
        meshformat.polygonCount = polygonCount

        for i,(polygon,uv) in enumerate(zip(polygonArray,UVarray)):
            meshformat.faces.append( [ i , [x for x in polygon] , uv[0] , uv[1] ] )


    #書き込み---------------------------------------------------
    export_data = []
    for mesh in meshArray:
        export_data.append( mesh.export() )

    export_pcl( filename , export_data)

#---------------------------------------------------------------------------------------
#mesh import
#---------------------------------------------------------------------------------------
def mesh_import( filename ):
    props = bpy.context.scene.kiaimportexport_props 
    for md in import_pcl(filename):
        mf = MeshFormat([])
        mf.getData( md ,props.scale )
        
        #メッシュの生成
        mesh_data = bpy.data.meshes.new("cube_mesh_data")
        mesh_data.from_pydata(mf.vtxarray, [], mf.polyarray)
        mesh_data.update()

        #UVの生成
        uvtex = utils.UV_new(mesh_data)

        uvtex.name = 'UVset'

        for i,face in enumerate(mesh_data.polygons):
            for loop_idx,u,v in zip(face.loop_indices,mf.uarray[i],mf.varray[i]):
                uv_coords = mesh_data.uv_layers.active.data[loop_idx].uv
                uv_coords.x = u
                uv_coords.y = v

        obj = bpy.data.objects.new(mf.name, mesh_data)

        scene = bpy.context.scene

        utils.sceneLink(obj)
        utils.select(obj,True)

        obj.matrix_world = mf.m_rot
        obj.location = mf.location



#---------------------------------------------------------------------------------------
#bone export
#---------------------------------------------------------------------------------------
def get_bonedata(v , loc , matrix):
    props = bpy.context.scene.kiaimportexport_props

    if props.upvector == 'Maya':
        vector = (v[0],v[2],v[1])
    elif props.upvector == 'Blender':
        vector = (v[0],v[1],v[2])

    #loc = Vector(bone.head)* props.scale
    #m0 = Matrix.Translation(loc) @ Matrix(bone.matrix).to_3x3().to_4x4()
    m0 = Matrix.Translation(loc) @ Matrix(matrix).to_3x3().to_4x4()
            
    if props.upvector == 'Maya':
        m0 = Matrix.Rotation(math.radians(-90.0), 3, "X").to_4x4() @ m0 

    m0.transpose()
    matrix = np.array(m0).flatten().tolist()

    return [matrix,vector]

        



def bone_export( filename ):
    props = bpy.context.scene.kiaimportexport_props

    obj = bpy.context.object
    bpy.ops.object.mode_set(mode='EDIT')

    bonearray = []

    for bone in obj.data.edit_bones:
        v = Vector(bone.tail) - Vector(bone.head)
        v.normalize()
        loc = Vector(bone.head)* props.scale
        
        matrix = Matrix( bone.matrix )
        #m = Matrix( bone.matrix )
        result = get_bonedata( v , loc, matrix )
        # if props.upvector == 'Maya':
        #     vector = (v[0],v[2],v[1])
        # elif props.upvector == 'Blender':
        #     vector = (v[0],v[1],v[2])

        # loc = Vector(bone.head)* props.scale
        # m0 = Matrix.Translation(loc) @ Matrix(bone.matrix).to_3x3().to_4x4()
               
        # if props.upvector == 'Maya':
        #     m0 = Matrix.Rotation(math.radians(-90.0), 3, "X").to_4x4() @ m0 

        # m0.transpose()
        # matrix = np.array(m0).flatten().tolist()

        
        # if bone.parent != None:
        #     parent = bone.parent.name
        # else:
        #     parent = ''

        if bone.parent != None:
            parent = bone.parent.name
        else:
            parent = ''


        #子供のリスト
        children = []
        print(bone.children)
        if bone.children != []:

            for c in bone.children:
                children.append(c.name)

        else:
            tip_loc = Vector(bone.tail) * props.scale
            tip_name = bone.name + '_tip'
            tip_name = tip_name.replace('.' , '_')
            #tip_matrix = 
            tip_parent = bone.name
            result0 = get_bonedata( v , tip_loc , matrix )
            bonearray.append([ tip_name, result0[0] ,result0[1] , tip_parent ,[] ])


        #bonearray.append([ bone.name , matrix ,vector , parent ,children ])
        bonearray.append([ bone.name.replace('.' , '_') , result[0] ,result[1] , parent ,children ])

    for b in bonearray:
        print(b)
    export_pcl(filename , bonearray)
    bpy.ops.object.mode_set(mode='OBJECT')


#---------------------------------------------------------------------------------------
#bone import
#[bone名,[child1,child2,..],(x,y,z)]
#---------------------------------------------------------------------------------------
def bone_import(filename):
    
    boneArray = {}
    bonenameArray = []

    for md in import_pcl(filename):
        b = Bone(md)#子供と親の取得

        boneArray[b.name] = b
        bonenameArray.append(b.name)

    #ジョイント生成
    bpy.ops.object.add(type='ARMATURE', enter_editmode=True, location=(0,0,0))
    amt = bpy.context.object
    bpy.ops.object.mode_set(mode='EDIT')

    for bn in bonenameArray:
        boneArray[bn].draw( amt ,boneArray)

    #すべてのボーンを生成してからペアレント処理
    for bn in bonenameArray:
        boneArray[bn].DoParent( boneArray )#ボーンの辞書配列を渡してペアレントに使う

    #tailを割り出すvectorと子供の内積が1ならばその子供の位置をtailにする >> draw


#---------------------------------------------------------------------------------------
#weight import
#オブジェクトモードなら全頂点のウェイトを読み込む　エディットモードなら選択した頂点だけ
#---------------------------------------------------------------------------------------
def weight_import(path):

    mode = True
    if utils.current_mode() == 'OBJECT':
        mode = False

    for obj in bpy.context.selected_objects:

        filename = '%s%s.wgt' % (path ,obj.name)

        #選択された頂点のインデックスのセットをつくり、ウェイトを描き戻すときにチェックする
        #インデックスは０から始まる
        selectedVtx = [v for v in obj.data.vertices if v.select]
        selectedVtxIndex = set([v.index for v in obj.data.vertices if v.select])


        #ウェイト値のクリア
        if mode:
            for v in selectedVtx:
                for i, g in enumerate(v.groups):
                    v.groups[i].weight=0
        else:            
            for v in obj.data.vertices:
                for i, g in enumerate(v.groups):
                    v.groups[i].weight=0

        #ウェイト値読み込む
        if mode:#edit mode 
            for i,point in enumerate(import_pci()):
                if i in selectedVtxIndex:
                    for w in point.findall('weight'):
                        vg = obj.vertex_groups[w[0]]
                        vg.add( [i], float(w[1]), 'REPLACE' )

        else:#object mode
            dat = import_pcl(filename)

            bonearray = dat.pop(0)
            for i,point in enumerate(dat):

                result = []
                for w in point:
                    vg = obj.vertex_groups[w[0]]
                    vg.add( [i], float(w[1]), 'REPLACE' )
                    result.append([w[0],w[1]])

#---------------------------------------------------------------------------------------
#weight export
#ウェイトフォーマット インデックスは含めない（リストの順番で対応）
#一つ目の要素にボーン名の配列
#[ [bone1 ,bon2 , ], [bonename , value] , [bonename , value] , . . . ]
#---------------------------------------------------------------------------------------
def weight_export__(path):
    #ボーン名
    bonearray = set()

    for obj in utils.selected():

        objname = obj.name
        boneArray = []
        for group in obj.vertex_groups:
            boneArray.append(group.name)

        #print(boneArray)
        size = len(boneArray)
        #頂点の情報
        msh = obj.data
        vtxCount = str(len(msh.vertices))#頂点数


        print(boneArray)
        export_data = []
        for v in msh.vertices:
            vtx = Vtx()
            #print('--------------------------------')
            wgt = [0.0]* size
            for vge in v.groups:
                if vge.weight > 0.00001 and vge.group < size :#ウェイト値０は除外 and prevent index out of range
                    #vtx.getWeight(vge.group, vge.weight ,boneArray) #boneArrayから骨名を割り出して格納
                    wgt[vge.group] = vge.weight
            #vtx.normalize_weight() #ウェイトをノーマライズする
            #print(wgt)
            # for bone in [x.name for x in vtx.weight]:
            #     bonearray.add(bone)

        #     export_data.append(vtx.export())


        # export_data.insert(0,list(bonearray))

        # filename = path + objname + '.wgt'
        # export_pcl( filename ,  export_data )

        # bpy.ops.object.mode_set(mode='OBJECT')



#---------------------------------------------------------------------------------------
#weight export
#ウェイトフォーマット インデックスは含めない（リストの順番で対応）
#一つ目の要素にボーン名の配列
#[ [bone1 ,bon2 , ], [bonename , value] , [bonename , value] , . . . ]
#---------------------------------------------------------------------------------------
def weight_export(path):
    #ボーン名
    bonearray = set()

    for obj in utils.selected():

        objname = obj.name
        boneArray = []
        for group in obj.vertex_groups:
            boneArray.append(group.name)

        #print(boneArray)
        size = len(boneArray)
        #頂点の情報
        msh = obj.data
        vtxCount = str(len(msh.vertices))#頂点数

        export_data = []
        for v in msh.vertices:
            vtx = Vtx()
            for vge in v.groups:
                if vge.weight > 0.00001 and vge.group < size :#ウェイト値０は除外 and prevent index out of range
                    vtx.getWeight(vge.group, vge.weight ,boneArray) #boneArrayから骨名を割り出して格納
            vtx.normalize_weight() #ウェイトをノーマライズする

            for bone in [x.name for x in vtx.weight]:
                bonearray.add(bone)

            export_data.append(vtx.export())


        export_data.insert(0,list(bonearray))

        filename = path + objname + '.wgt'
        export_pcl( filename ,  export_data )

        bpy.ops.object.mode_set(mode='OBJECT')


#---------------------------------------------------------------------------------------
#animation Export
#ボーン単位でプロットして出力する。フレーム単位では骨の姿勢のアップデートがうまくいかなかった
#フォーマット 第一要素にヘッダー
# [ [startframe , enndframe ]] ,  [ bonename ,[ [m0,m1,..,m15] , [m0,m1,..,m15] ]] ,  [ bonename,[m0,m1,..,m15] ] ,....  ]
#---------------------------------------------------------------------------------------
def anim_export(filename):
    props = bpy.context.scene.kiaimportexport_props
    
    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end

    exportdata = [ [start,end] ]
    
    amt = bpy.context.active_object
    num = len(amt.pose.bones)

    for f in range(end):    
        bpy.context.scene.frame_set(f)
    
        animarray = []
        for b in amt.pose.bones:       
            #m0 = Matrix(b.matrix)
            loc = Vector(b.head)* props.scale
            m0 = Matrix.Translation(loc) @ Matrix(b.matrix).to_3x3().to_4x4()


            if props.upvector == 'Maya':
                m0 = Matrix.Rotation(math.radians(-90.0), 3, "X").to_4x4() @ m0 

            m0.transpose()

            matrix = np.array(m0).flatten().tolist()
            animarray.append([b.name,matrix])

        exportdata.append(animarray)

    export_pcl( filename ,  exportdata )


# def anim_export_(filename):
#     props = bpy.context.scene.kiaimportexport_props
    
#     start = bpy.context.scene.frame_start
#     end = bpy.context.scene.frame_end

#     exportdata = [ [start,end] ]
    
#     amt = bpy.context.active_object
#     num = len(amt.pose.bones)

#     for i,b in enumerate(amt.pose.bones):
#         print('%d/%d' % (i,num))
#         animarray = []
#         for f in range(end):
#             bpy.context.scene.frame_set(f)

#             m0 = Matrix(b.matrix)

#             if props.upvector == 'Y':
#                 m0 = Matrix.Rotation(math.radians(-90.0), 3, "X").to_4x4() @ m0 

#             m0.transpose()

#             matrix = np.array(m0).flatten().tolist()
#             animarray.append(matrix)

#         exportdata.append([b.name , animarray])

#     export_pcl( filename ,  exportdata )

#選択した骨にアニメーションをインポート
def anim_import(filename):
    amt = bpy.context.active_object

    alldata = import_pcl(filename)
    header = alldata.pop(0)

    allbonename = [b.name for b in amt.pose.bones]


    for f,data in enumerate(alldata):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()

        for bone in data:
            name = bone[0]
            m = bone[1]

            if name in allbonename:
                b = amt.pose.bones[name]
                matrix = Matrix([m[0:4],m[4:8],m[8:12],m[12:16]])
                
                matrix.transpose()
                b.matrix = matrix
                b.keyframe_insert(data_path="location")
                b.keyframe_insert(data_path="rotation_quaternion")


# #選択した骨にアニメーションをインポート
# def anim_import_(filename):
#     amt = bpy.context.active_object

#     alldata = import_pcl(filename)
#     header = alldata.pop(0)

#     allbonename = [b.name for b in amt.pose.bones]
#     for data in alldata:
#         name = data[0]
#         for f,m in enumerate(data[1]):
#             bpy.context.scene.frame_set(f)
#             bpy.context.view_layer.update()

#             if name in allbonename:
#                 b = amt.pose.bones[name]
#                 matrix = Matrix([m[0:4],m[4:8],m[8:12],m[12:16]])
#                 matrix.transpose()
#                 b.matrix = matrix
#                 b.keyframe_insert(data_path="location")
#                 b.keyframe_insert(data_path="rotation_quaternion")




#---------------------------------------------------------------------------------------
#FBX Export
#---------------------------------------------------------------------------------------
# def export_fbx():
#     #出力モード設定
#     mode = bpy.context.scene.export_selected_export_option
#     scale = bpy.context.scene.export_selected_fbx_scale
#     outpath = bpy.context.scene.export_selected_fbx_path

#     if mode == 'def':
#         bpy.ops.export_scene.fbx(filepath=outpath ,global_scale = scale , use_selection = True)

#     elif mode == 'md':
#         bpy.ops.export_scene.fbx(filepath=outpath ,global_scale = scale , bake_anim_step=2.0 , bake_anim_simplify_factor=0.0 , use_selection = True)

#---------------------------------------------------------------------------------------
#FBXエクスポート
#sel ファイル名をアクティブなモデルの名前とする
#col 選択したコレクション
#md マーベラスデザイナーでアニメーションの再生が正しく行われるようなオプション
#---------------------------------------------------------------------------------------


Collections = set()

#コレクションの子供コレクションを再帰的に調べて全部取得する
def get_col( x ):
    Collections.add(x.name)
    for col in x.children.keys():
        self.get_col(x.children[col])

#ファイル名として正しく修正
def correct_name(name):
    return name.replace( '.' , '_' ).replace( ' ' , '_' )

def export_format(mode):
    props = bpy.context.scene.kiaimportexport_props 
    outpath = props.fbx_path


    if outpath[-1] != '\\' and outpath[-1] != '/':
        outpath += '/'


    if props.export_option == 'sel':
        outpath += '%s.%s' % (correct_name( utils.getActiveObj().name ) , mode)

    elif props.export_option == 'col':
        Collections.clear()
        utils.deselectAll()

        col = utils.collection.get_active()
        get_col( col )
        
        outpath += '%s.%s' % (correct_name( col.name ) , mode)

        #選択されたコレクションにリンクされたオブジェクトを取得
        for ob in bpy.context.scene.objects: 
            if ob.users_collection[0].name in Collections: 
                utils.select(ob,True)


    forward = props.axis_forward
    up = props.axis_up

    if props.export_mode == 'def':
        print(outpath)
        if mode == 'fbx':
            bpy.ops.export_scene.fbx(
                filepath=outpath ,
                use_selection = True ,
                global_scale = props.scale ,
                axis_forward = props.axis_forward ,
                axis_up = props.axis_up
                )

        elif mode == 'obj':
            bpy.ops.export_scene.obj(
                filepath=outpath ,
                use_selection = True ,
                global_scale = props.scale ,
                axis_forward = props.axis_forward ,
                axis_up = props.axis_up
                )

    elif props.export_mode == 'ue':
        print(outpath)
        if mode == 'fbx':
            bpy.ops.export_scene.fbx(
                filepath=outpath ,
                use_selection = True ,
                global_scale = props.scale ,
                axis_forward = props.axis_forward ,
                axis_up = props.axis_up,
                mesh_smooth_type = 'FACE',#Added for UE
                add_leaf_bones  = False , #Added for UE
                use_armature_deform_only  = True #Added for UE
                )

        elif mode == 'obj':
            bpy.ops.export_scene.obj(
                filepath=outpath ,
                use_selection = True ,
                global_scale = props.scale ,
                axis_forward = props.axis_forward ,
                axis_up = props.axis_up
                )


    elif props.export_mode == 'md':
        if mode == 'fbx':
            bpy.ops.export_scene.fbx(filepath=outpath ,global_scale = props.scale , bake_anim_step=2.0 , bake_anim_simplify_factor=0.0 , use_selection = True)
        elif mode == 'obj':
            bpy.ops.export_scene.obj(filepath=outpath ,global_scale = props.scale , use_selection = True)
        