import numpy as np
import bpy
from bpy.props import FloatProperty

from mathutils import (Vector , Matrix)
import pickle
import imp

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
        if obj != []:
            self.name = obj.name
            m = Matrix(obj.matrix_world).to_3x3()
    
            self.m_rot = []
            for i in range(3):
                self.m_rot.append( [x for x in m[i]] )

            self.location = [x for x in obj.location ]
            print(self.location)

        
        self.points = [] #頂点の配列 [ index , [ x ,y , z ] ]
        self.faces = [] #ポリゴンの配列　[ index, vertexarray[] , uarray[] , varray[] ] 
        
    
    def export(self):
        return [ [ self.name , self.vtxCount , self.polygonCount , self.m_rot ,self.location ] , self.points , self.faces ]

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
            w.value = str(w.value/sum)

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
        print(val)
        x = np.array(val.split(' ')[:-1])#配列の最後が''になるので削除
        print(x)
        self.head = x.astype(np.float)

    def SetTail(self,val):
        x = np.array(val.split(' ')[:-1])
        self.tail = x.astype(np.float)

    def SetMatrix(self,val):
        x = np.array(val.split(' ')[:-1])
        vec = x.astype(np.float)
        print(vec[0:4] , vec[4:8],vec[8:12],vec[12:16])
        self.matrix = mathutils.Matrix([vec[0:4],vec[4:8],vec[8:12],vec[12:16]])


    def draw(self,amt , dic):
        self.bone = amt.data.edit_bones.new(self.name)
        self.bone.head = self.head

        #tailを割り出す
        # vectorと子供の内積が1ならばその子供の位置をtailにする
        #対象の子供があった場合、その子供のジョイントのコネクトフラグをＯＮにする
        if self.childlen != []:
            print(self.childlen,'vector>>', dic[self.childlen[0]].head)
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

        #頂点の情報
        vtxCount = str(len(vertices))#頂点数
        vtxArray = []
        for v in vertices:
            vtx = Vtx()
            vtxArray.append(vtx)
            vtx.co = v.co * props.scale

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
def bone_export( filename ):
    obj = bpy.context.object
    bpy.ops.object.mode_set(mode='EDIT')

    bonearray = []
    for bone in obj.data.edit_bones:

        v = Vector(bone.tail) - Vector(bone.head)
        v.normalize()
        vector = (v[0],v[1],v[2])


        m0 = Matrix(bone.matrix)
        m0.transpose()
        matrix = np.array(m0).flatten().tolist()

        
        if bone.parent != None:
            parent = bone.parent.name
        else:
            parent = ''

        #子供のリスト
        children = []
        if bone.children != ():

            for c in bone.children:
                children.append(c.name)

        bonearray.append([ bone.name , matrix ,vector , parent ,children ])

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
def weight_import():

    mode = True
    if utils.current_mode() == 'OBJECT':
        mode = False

    for obj in bpy.context.selected_objects:

        filename = '%s.wgt' % obj.name

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
        if mode:
            for i,point in enumerate(import_pci()):
                if i in selectedVtxIndex:
                    for w in point.findall('weight'):
                        vg = obj.vertex_groups[w[0]]
                        vg.add( [i], float(w[1]), 'REPLACE' )

        else:
            dat = import_pcl(filename)
            bonearray = dat.pop(0)
            for i,point in enumerate(dat):
                for w in point:
                    vg = obj.vertex_groups[w[0]]
                    vg.add( [i], float(w[1]), 'REPLACE' )



#---------------------------------------------------------------------------------------
#weight export
#ウェイトフォーマット インデックスは含めない（リストの順番で対応）
#一つ目の要素にボーン名の配列
#[ [bone1 ,bon2 , ], [bonename , value] , [bonename , value] , . . . ]
#---------------------------------------------------------------------------------------
def weight_export():
    #ボーン名
    bonearray = set()

    for obj in utils.selected():

        objname = obj.name
        boneArray = []
        for group in obj.vertex_groups:
            boneArray.append(group.name)


        #頂点の情報
        msh = obj.data
        vtxCount = str(len(msh.vertices))#頂点数

        export_data = []
        for v in msh.vertices:
            vtx = Vtx()
            for vge in v.groups:
                if vge.weight > 0.00001:#ウェイト値０は除外
                    vtx.getWeight(vge.group, vge.weight ,boneArray) #boneArrayから骨名を割り出して格納
            vtx.normalize_weight() #ウェイトをノーマライズする

            for bone in [x.name for x in vtx.weight]:
                bonearray.add(bone)

            export_data.append(vtx.export())


        export_data.insert(0,list(bonearray))

        filename = objname + '.wgt'
        print(export_data)
        export_pcl( filename ,  export_data )

        bpy.ops.object.mode_set(mode='OBJECT')



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

def export_fbx():
    props = bpy.context.scene.kiaimportexport_props 
    outpath = props.fbx_path


    if outpath[-1] != '\\' and outpath[-1] != '/':
        outpath += '/'


    if props.export_option == 'sel':
        outpath += correct_name( utils.getActiveObj().name ) + '.fbx'

    elif props.export_option == 'col':
        Collections.clear()
        utils.deselectAll()

        col = utils.collection.get_active()
        get_col( col )
        
        outpath += correct_name( col.name ) + '.fbx'

        #選択されたコレクションにリンクされたオブジェクトを取得
        for ob in bpy.context.scene.objects: 
            if ob.users_collection[0].name in Collections: 
                utils.select(ob,True)


    if props.export_mode == 'def':
        #bpy.ops.export_scene.fbx(filepath=outpath ,global_scale = props.scale , use_selection = True)
        print(outpath)
        bpy.ops.export_scene.fbx(filepath=outpath , use_selection = True )

    elif props.export_mode == 'md':
        bpy.ops.export_scene.fbx(filepath=outpath ,global_scale = props.scale , bake_anim_step=2.0 , bake_anim_simplify_factor=0.0 , use_selection = True)
        