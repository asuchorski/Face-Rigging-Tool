import maya.cmds as cmds
import math

'''
IMPORTANT

Before running the script change line 611 to your own script directory so the images in the ui can be found

'''


selected_faces = []
generated_joints = []

def auto_skin(*args):
    '''Gets all children of the root joint, filters out joints
    that are not needed and binds the joints to the mesh
    '''
    root_joint = 'head_joint'
    child_joints = cmds.listRelatives(root_joint, allDescendents=True, type='joint')
    filtered_joints = [j for j in child_joints if j not in ['left_eye_joint', 'right_eye_joint']]
    # Select all remaining joints
    cmds.select(filtered_joints+['Head'])
    # Skin bind the selected joints to the selected mesh
    skin_cluster = cmds.skinCluster(filtered_joints, 'Head', toSelectedBones=True,  normalizeWeights=1, bindMethod=1, skinMethod=1, ignoreHierarchy=True)
    
   
def add_face_selection(*args):
    '''stores selected face in a list when the user adds the face selection
    ensures that the selected face is in the correct format and that it is selected.
    '''
    # Get the selected faces of the mesh
    sel = cmds.ls(selection=True)
    if not sel:
        cmds.warning('Please select faces on the mesh')
        return
        
    sel_split = sel[0].split('.')
    if len(sel_split) == 2 and sel_split[1].startswith('f['):
        mesh = sel_split[0]
        faces = sel_split[1].replace('f[', '').replace(']', '').split(',')
        face_indices = [int(f) for f in faces]
    elif len(sel_split) == 2 and sel_split[1].startswith('f'):
        mesh = sel_split[0]
        face_indices = [int(sel_split[1].split('f')[1])]
    else:
        cmds.warning('Please select faces on the mesh in the format "mesh.f[#]" or "mesh.f[#,#,#]"')
        return

    # Store the selected faces
    global selected_faces
    selected_faces += [(mesh, face_indices)]
    cmds.warning('Selected face stored')
    
def create_joints(*args):
    '''Generates joints on the face from the stored face selection
    '''
    global selected_faces
    if not selected_faces:
        cmds.warning('Please select the specified faces on the mesh')
        return
    
    radius=calculate_mesh_width('Head')
    global generated_joints
    for jnt in generated_joints:
        # Delete previously generated joints if there was any
        cmds.delete(jnt)
    generated_joints = []
    cmds.select(clear=True)
    for sel in selected_faces:
        mesh, face_indices = sel
        for index in face_indices:
            # Get the vertices of the face
            face_verts = cmds.polyListComponentConversion(mesh+'.f[%d]' % index, toVertex=True)
            face_verts = cmds.ls(face_verts, flatten=True)
            # Calculate the average position of the 4 vertices to find the middle of the face
            avg_pos = [0.0, 0.0, 0.0]
            for vert in face_verts:
                pos = cmds.pointPosition(vert, world=True)
                avg_pos[0] += pos[0]
                avg_pos[1] += pos[1]
                avg_pos[2] += pos[2]
            avg_pos[0] /= len(face_verts)
            avg_pos[1] /= len(face_verts)
            avg_pos[2] /= len(face_verts)
            
            # Create the joint at the average position with the calculated automatic radius
            jnt = cmds.joint(position=(avg_pos[0],avg_pos[1],avg_pos[2]), radius=radius)
            generated_joints.append(jnt)
        cmds.select(clear=True)

    cmds.warning('Joints generated')
    rename_all_joints()
    create_right_eye()
    create_left_eye()
    
def clear_face_selections(*args):
    '''clears out the list of stored faces
    '''
    global selected_faces
    selected_faces = []
    cmds.warning('Face selections cleared')

def delete_generated_joints(*args):
    '''deletes all generated joints
    '''
    global generated_joints
    for jnt in generated_joints:
        cmds.delete(jnt)
    generated_joints = []
    cmds.warning('Generated joints deleted')
    
def select_all_joints(*args):
    cmds.select(generated_joints)
    
def mirror_joints(*args):
    '''Mirrors the _L joints to the other side and renames them
    parents the joints
    '''
    all_objects = cmds.ls()
    selected_objects = []
    for obj in all_objects:
        if obj.endswith("_joint_L"):
            selected_objects.append(obj)
        print(selected_objects)
    #loop through the joint list and mirror them to the other side
    for joint in selected_objects:
        mirrored_joint = cmds.mirrorJoint(joint, mirrorYZ=True, mirrorBehavior=True, searchReplace=('_L', '_R'))
        if mirrored_joint:
            generated_joints.append(mirrored_joint[0])
    
    #parent the joints
    head_parent_joint="head_joint"
    head_child_joint="mouth_inside_joint_1","mouth_inside_joint_2",\
    "mouth_inside_joint_3","mouth_inside_joint_7","mouth_inside_joint_8"
    cmds.parent(head_child_joint, head_parent_joint)
    
    cmds.parent('mouth_top_middle_joint', 'mouth_inside_joint_1')
    cmds.parent('mouth_top_side_joint_L', 'mouth_inside_joint_2')
    cmds.parent('mouth_top_tip_joint_L', 'mouth_inside_joint_3')
    cmds.parent('mouth_bottom_middle_joint', 'mouth_inside_joint_4')
    cmds.parent('mouth_bottom_side_joint_L', 'mouth_inside_joint_5')
    cmds.parent('mouth_bottom_tip_joint_L', 'mouth_inside_joint_6')
    
    cmds.parent('mouth_top_side_joint_R', 'mouth_inside_joint_7')
    cmds.parent('mouth_top_tip_joint_R', 'mouth_inside_joint_8')
    cmds.parent('mouth_bottom_side_joint_R', 'mouth_inside_joint_9')
    cmds.parent('mouth_bottom_tip_joint_R', 'mouth_inside_joint_10')
    
    mouth_parent_joint="jaw_joint"
    mouth_child_joint="mouth_inside_joint_4","mouth_inside_joint_5","mouth_inside_joint_6",\
    "mouth_inside_joint_9","mouth_inside_joint_10"
    cmds.parent(mouth_child_joint, mouth_parent_joint)
    cmds.select(clear=True)
            
def create_joint_at_center(joint_name, mesh_name):
    '''using the world bounding box of the mesh, it creates a joint at the centre of the mesh
    '''
    bbox = cmds.exactWorldBoundingBox(mesh_name)
    center = [(bbox[0] + bbox[3]) / 2.0, (bbox[1] + bbox[4]) / 2.0, (bbox[2] + bbox[5]) / 2.0]
    radius=calculate_mesh_width('Head')
    joint = cmds.joint(name = joint_name,position=center, radius=radius)
    generated_joints.append(joint)
    
def create_right_eye(*args):
    #set the name of the joint and mesh and pass that to create_joint_at_center
    joint_name = 'right_eye_joint'
    mesh_name = 'Right_eye'
    create_joint_at_center(joint_name,mesh_name)
    cmds.select(clear=True)
    
def create_left_eye(*args):
    #set the name of the joint and mesh and pass that to create_joint_at_center
    joint_name = 'left_eye_joint'
    mesh_name = 'Left_eye'
    create_joint_at_center(joint_name,mesh_name)
    cmds.select(clear=True)
    
def create_head_joint(*args):
    '''create the head joint and moves joints back into position
    '''
    joint_name = 'head_joint'
    mesh_name = 'Head'
    create_joint_at_center(joint_name,mesh_name)
    create_jaw()
    create_mouth_joints()
    
    #parent the eyes to head and move the eyes back into position
    head_joint = cmds.xform('head_joint', query=True, worldSpace=True, translation=True)
    left_eye_joint = cmds.xform('left_eye_joint', query=True, worldSpace=True, translation=True)
    right_eye_joint = cmds.xform('right_eye_joint', query=True, worldSpace=True, translation=True)
    
    parent_them('left_eye_joint','head_joint')
    parent_them('right_eye_joint','head_joint')
    
    cmds.move(left_eye_joint[0],left_eye_joint[1],left_eye_joint[2],'left_eye_joint')
    cmds.move(right_eye_joint[0],right_eye_joint[1],right_eye_joint[2],'right_eye_joint')
    
    #parent the rest of the joints
    parent_joints()
    
def create_jaw(*args):
    '''get the average  Y and Z pos of the cheek and head joint, use that to create the jaw joint between them
    '''
    cmds.select(clear=True)
    radius=calculate_mesh_width('Head')
    cheek_joint_position = cmds.xform('cheek_joint_L ', query=True, worldSpace=True, translation=True)
    head_joint_position = cmds.xform('head_joint', query=True, worldSpace=True, translation=True)
    average_Z = ((head_joint_position[2] + cheek_joint_position[2])/2)
    average_Y = ((head_joint_position[1] + cheek_joint_position[1])/2)
    cmds.joint(name='jaw_joint',position=(0,average_Y,average_Z), radius=radius)
    
def create_mouth_joints(*args):
    '''get the average Z pos of the cheek and jaw joint, use that to create a mouth joint between them
    '''
    cmds.select(clear=True)
    radius=calculate_mesh_width('Head')
    cheek_joint_position = cmds.xform('cheek_joint_L', query=True, worldSpace=True, translation=True)
    mouth_top_middle_joint_position = cmds.xform('mouth_top_middle_joint', query=True, worldSpace=True, translation=True)
    jaw_joint_position = cmds.xform('jaw_joint', query=True, worldSpace=True, translation=True)
    average_Z = ((cheek_joint_position[2] + jaw_joint_position[2])/2)
    name_count=1
    #loop through to create 10 mouth inside joints, 5 for the bottom lip, 5 for the top
    for i in range(10):
        cmds.joint(name='mouth_inside_joint_'+str(name_count),position=(0,mouth_top_middle_joint_position[1],average_Z), radius=radius)
        cmds.select(clear=True)
        name_count+=1
    
def create_eye_controls(*args):
    '''use the eye joint positions and the calculated mesh width to create and position eye controls
    '''
    radius=calculate_mesh_width('Head')
    pos_right_eye = cmds.xform('right_eye_joint', query=True, translation=True, worldSpace=True)
    pos_left_eye = cmds.xform('left_eye_joint', query=True, translation=True, worldSpace=True)
    cmds.circle(name = 'right_eye_control',nr=(0, 0, 0),r=(radius/2),center=(pos_right_eye[0],pos_right_eye[1],pos_right_eye[2]+(2*radius)))
    cmds.xform('right_eye_control', centerPivots=True)
    cmds.circle(name = 'left_eye_control',nr=(0, 0, 0),r=(radius/2),center=(pos_left_eye[0],pos_left_eye[1],pos_left_eye[2]+(2*radius)))
    cmds.xform('left_eye_control', centerPivots=True)
    cmds.circle(name = 'eyes_control',nr=(0, 0, 0),r=(1.5*radius),center=(0,pos_left_eye[1],pos_left_eye[2]+(2*radius)))
    cmds.xform('eyes_control', centerPivots=True)
    cvs = cmds.ls("{0}.cv[*]".format('eyes_control'), flatten=True)
    cmds.move(0, -(1.7*radius), 0, "{0}.cv[1]".format('eyes_control'), relative=True)
    cmds.move(0, (1.7*radius), 0, "{0}.cv[5]".format('eyes_control'), relative=True)
    colour_red('right_eye_control')
    colour_blue('left_eye_control')
    colour_yellow('eyes_control')
    
def contrain_eyes(*args):
    '''aim constraint eyes to joints and skin them
    '''
    #clean up unwanted controls
    cmds.delete('right_eye_joint_anim','left_eye_joint_anim')
    cmds.aimConstraint('left_eye_control', 'left_eye_joint', aimVector=[1,0,0], upVector=[0,1,0], worldUpType="vector", maintainOffset=True)
    cmds.aimConstraint('right_eye_control', 'right_eye_joint', aimVector=[1,0,0], upVector=[0,1,0], worldUpType="vector", maintainOffset=True)
    cmds.parent('left_eye_control', 'eyes_control')
    cmds.parent('right_eye_control', 'eyes_control')
    
    cmds.select('left_eye_joint')
    cmds.skinCluster('left_eye_joint', 'Left_eye', toSelectedBones=True)
    cmds.select('right_eye_joint')
    cmds.skinCluster('right_eye_joint', 'Right_eye', toSelectedBones=True)
    cmds.select(clear=True)

    
def rename_all_joints(*args):
    '''rename the joints the user has selected in order to new names, matching what they're supposed to be
    '''
    cmds.rename('joint1','eyebrow_01_joint_L')
    cmds.rename('joint2','eyebrow_02_joint_L')
    cmds.rename('joint3','eyebrow_03_joint_L')
    cmds.rename('joint4','eyelid_top_01_joint_L')
    cmds.rename('joint5','eyelid_top_02_joint_L')
    cmds.rename('joint6','eyelid_top_03_joint_L')
    cmds.rename('joint7','eyelid_bottom_01_joint_L')
    cmds.rename('joint8','eyelid_bottom_02_joint_L')
    cmds.rename('joint9','eyelid_bottom_03_joint_L')
    cmds.rename('joint10','nose_side_joint_L')
    cmds.rename('joint11','nose_fold_joint_L')
    cmds.rename('joint12','squint_01_joint_L')
    cmds.rename('joint13','squint_02_joint_L')
    cmds.rename('joint14','ear_joint_L')
    cmds.rename('joint15','mouth_top_middle_joint')
    cmds.rename('joint16','mouth_top_side_joint_L')
    cmds.rename('joint17','mouth_top_tip_joint_L')
    cmds.rename('joint18','mouth_bottom_middle_joint')
    cmds.rename('joint19','mouth_bottom_side_joint_L')
    cmds.rename('joint20','mouth_bottom_tip_joint_L')
    cmds.rename('joint21','chin_joint')
    cmds.rename('joint22','brow_middle_joint')
    cmds.rename('joint23','nose_tip_joint')
    cmds.rename('joint24','cheek_joint_L')
    
def parent_joints(*args):
    '''parent all the joints that should be parented directly to the head to the head
    '''
    head_parent_joint="head_joint"
    head_child_joint="eyebrow_01_joint_L", "eyebrow_02_joint_L","eyebrow_03_joint_L",\
    "eyelid_top_01_joint_L","eyelid_top_02_joint_L","eyelid_top_03_joint_L",\
    "eyelid_bottom_01_joint_L","eyelid_bottom_02_joint_L","eyelid_bottom_03_joint_L",\
    "nose_side_joint_L","nose_fold_joint_L","squint_01_joint_L",\
    "squint_02_joint_L","ear_joint_L","brow_middle_joint",\
    "brow_middle_joint","cheek_joint_L","jaw_joint",\
    "nose_tip_joint"
    cmds.parent(head_child_joint, head_parent_joint)
    cmds.parent('chin_joint', 'jaw_joint')
    cmds.select(clear=True)
    
def create_controls(*args):
    '''create all the face controls as nurbs circles, with an automatic radius to match the face
    '''
    face_controls_list = []
    joint_list = []
    # List of joint names
    joints = cmds.ls(type='joint')
    # Iterate through each joint
    diameter=measure_joint_distance('ear_joint_L', 'ear_joint_R')
    for joint in joints:
        # Get the position of the joint and place the created control there, rename it to the name of the joint+_anim
        pos = cmds.xform(joint, query=True, worldSpace=True, translation=True)
        circle_name = joint + '_anim'
        cmds.circle(n=circle_name,radius=diameter/4)
        
        cmds.move(pos[0],pos[1],pos[2],circle_name)
        
        face_controls_list.append(circle_name)
        joint_list.append(joint)
        mesh_name = 'Head'

        cmds.select(clear=True)
     
    for j in face_controls_list:
        '''iterate through the creatd controls. If they are located on the +X axis, colour them red
        if they're located on the -X axis, colour them blue
        '''
        control_pos = cmds.xform(j, q=True, t=True, ws=True)
        #print("Position of " + j + ": x=" + str(control_pos[0]) + ", y=" + str(control_pos[1]) + ", z=" + str(control_pos[2]))
        if control_pos[0]>0:
            colour_blue(j)
        else:
            colour_red(j)
            
    #move the face controls slightly away from the mesh
    move_amount = (0, 0, diameter/4)

    # Loop through each circle and move its CVs
    for circle in face_controls_list:
        cv_positions = cmds.getAttr(circle + ".cv[*]")
        new_cv_positions = [(p[0] + move_amount[0], p[1] + move_amount[1], p[2] + move_amount[2]) for p in cv_positions]
        cmds.setAttr(circle + ".cv[*]", *sum(new_cv_positions, ()))
            
    diameter = measure_joint_distance('ear_joint_L', 'ear_joint_R')
    
    #colour the middle joints yellow
    colour_yellow('brow_middle_joint_anim')
    colour_yellow('nose_tip_joint_anim')
    colour_yellow('mouth_top_middle_joint_anim')
    colour_yellow('mouth_bottom_middle_joint_anim')
    colour_yellow('chin_joint_anim')
    
    #create the remaining more complicated controls    
    create_arrow_circle()
    create_eye_controls()
    adjust_controls()
    parent_controls(face_controls_list,joint_list)
    contrain_eyes()
    
def create_arrow_circle(*args):
    '''creates a circle with four arrows on the sides. Used to control the whole eyebrow movement, and mouth movement
    '''
    circle = cmds.circle(name='mouth_whole_anim', ch=False)[0]
    
    arrow = cmds.curve(name='arrow', d=1, p=[(-0.5, 0, -1), (0, 0, 0), (-0.5, 0, 1)],)
    
    # duplicate and rotate arrow to create all four arrows
    arrow_names = ['arrow_left', 'arrow_right', 'arrow_up', 'arrow_down']
    for i in range(4):
        arrow_dup = cmds.duplicate(arrow, name=arrow_names[i])[0]
        cmds.parent(arrow_dup, circle)
    
    cmds.rotate(90, 0, 0, 'arrow_left', r=True)
    cmds.rotate(90, 180, 0, 'arrow_right', r=True)
    cmds.rotate(90, 0, 90, 'arrow_up', a=True)
    cmds.rotate(90, 0, -90, 'arrow_down', a=True)
    cmds.move(1.384,0,0,'arrow_left')
    cmds.move(-1.385,0,0,'arrow_right')
    cmds.move(0,1.226,0,'arrow_up')
    cmds.move(0,-1.225,0,'arrow_down')
    
    shape = cmds.listRelatives('arrow_left', shapes=True)
    # cleanup
    cmds.select(clear=True)
    # cleanup
    cmds.delete(arrow)
    #move into place
    mouth_pos = cmds.xform('mouth_top_tip_joint_L', query=True, worldSpace=True, translation=True)
    eyebrow_pos_R = cmds.xform('eyebrow_03_joint_L', query=True, worldSpace=True, translation=True)
    eyebrow_pos_L = cmds.xform('eyebrow_03_joint_R', query=True, worldSpace=True, translation=True)
    
    diameter=measure_joint_distance('ear_joint_L', 'ear_joint_R')
    
    #scale the controls to the correct scale, move them into the correct places and assign a colour
    cmds.duplicate('mouth_whole_anim', name='eyebrow_whole_anim_L')
    cmds.duplicate('mouth_whole_anim', name='eyebrow_whole_anim_R')
    cmds.move(mouth_pos[0]+(2*diameter),mouth_pos[1],mouth_pos[2],'mouth_whole_anim')
    cmds.move(eyebrow_pos_R[0]+diameter,eyebrow_pos_R[1],eyebrow_pos_R[2],'eyebrow_whole_anim_L')
    cmds.move(eyebrow_pos_L[0]-diameter,eyebrow_pos_L[1],eyebrow_pos_L[2],'eyebrow_whole_anim_R')
    
    cmds.scale(diameter,diameter,diameter, 'mouth_whole_anim')
    cmds.scale(diameter/1.5,diameter/1.5,diameter/1.5, 'eyebrow_whole_anim_L','eyebrow_whole_anim_R')
    
    mouth_pivot = cmds.xform("mouth_inside_joint_1", q=True, rotatePivot=True, worldSpace=True)
    cmds.move(mouth_pivot[0], mouth_pivot[1], mouth_pivot[2], "mouth_whole_anim.rotatePivot", absolute=True)
    
    #also scale the jaw control to the correct scale
    cmds.scale(diameter/2,diameter/2,diameter/2,"jaw_joint_anim", dso=True)

    cmds.select('eyebrow_whole_anim_L', 'eyebrow_whole_anim_R', 'mouth_whole_anim')
    cmds.DeleteHistory()
    cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
    cmds.select(clear=True)
    colour_blue('eyebrow_whole_anim_L')
    colour_red('eyebrow_whole_anim_R')
    colour_yellow('mouth_whole_anim')
    cmds.select(clear=True)
    
def adjust_controls(*args):
    '''rotation adjustments of controls to fit the face
    '''
    cmds.rotate(0,45,0,'cheek_joint_L_anim','squint_02_joint_L_anim','eyebrow_03_joint_L_anim','eyelid_top_03_joint_L_anim','eyelid_bottom_03_joint_L_anim','mouth_top_tip_joint_L_anim','mouth_bottom_tip_joint_L_anim','nose_side_joint_L_anim')
    cmds.rotate(0,-45,0,'cheek_joint_R_anim','nose_side_joint_R_anim','squint_02_joint_R_anim','eyebrow_03_joint_R_anim','eyelid_bottom_03_joint_R_anim','eyelid_top_03_joint_R_anim','mouth_top_tip_joint_R_anim','mouth_bottom_tip_joint_R_anim')
    cmds.rotate(0,-90,0,'ear_joint_R_anim')
    cmds.rotate(0,90,0,'ear_joint_L_anim')
    cmds.rotate(0,-30,0,'mouth_top_side_joint_R_anim','mouth_bottom_side_joint_R_anim','squint_01_joint_R_anim')
    cmds.rotate(0,30,0,'mouth_top_side_joint_L_anim','mouth_bottom_side_joint_L_anim','squint_01_joint_L_anim')
    
    diameter=calculate_mesh_width('Head') 
    cmds.delete('head_joint_anim')
    cmds.circle(n='head_joint_anim', r=diameter*3)
    # Get the current position of the head pivot
    head_pivot = cmds.xform("head_joint", q=True, rotatePivot=True, worldSpace=True)
    #move the control above the  head using the calculated distance based on the mesh width
    cmds.move(head_pivot[0], head_pivot[1]+(diameter*4.5), head_pivot[2], "head_joint_anim", relative=True, rotatePivotRelative=True)
    cmds.rotate(-90,0,0,"head_joint_anim",relative=True)
    # Move the pivot back to its original position
    cmds.move(head_pivot[0], head_pivot[1], head_pivot[2], "head_joint_anim.rotatePivot", absolute=True)
    colour_green('head_joint_anim')
    
    #create jaw joint control and move into place
    cmds.delete('jaw_joint_anim')
    cmds.circle(n='jaw_joint_anim', r=diameter/2)
    jaw_pivot = cmds.xform("jaw_joint", q=True, rotatePivot=True, worldSpace=True)
    chin_pivot = cmds.xform("chin_joint", q=True, rotatePivot=True, worldSpace=True)

    cmds.move(chin_pivot[0], chin_pivot[1], chin_pivot[2]+diameter/3, "jaw_joint_anim", relative=True, rotatePivotRelative=True)
    cmds.move(jaw_pivot[0], jaw_pivot[1], jaw_pivot[2], "jaw_joint_anim.rotatePivot", absolute=True)
    
    cmds.move(0, 0, 0, "{0}.cv[1]".format('jaw_joint_anim'), relative=True)
    cmds.move(0, diameter/6, -(diameter), "{0}.cv[5]".format('jaw_joint_anim'), relative=True)
    cmds.move(0, diameter/12, -(diameter/2), "{0}.cv[6]".format('jaw_joint_anim'), relative=True)
    cmds.move(0, diameter/12, -(diameter/2), "{0}.cv[4]".format('jaw_joint_anim'), relative=True)
    colour_yellow('jaw_joint_anim')
    
    all_objects = cmds.ls()
    # Loop through all objects and select those that end in "anim"
    for obj in all_objects:
        if obj.endswith("anim"):
            cmds.select(obj)
            cmds.DeleteHistory()
            cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
    clean_up()
    return 0
    
def parent_controls(face_controls_list,joint_list):
    '''loop through joint and controls lists and parent constraint the controls to the joints
    '''
    for i in range(len(joint_list)):
        joint = joint_list[i]
        control = face_controls_list[i]
        constraint_name = cmds.parentConstraint(control, joint)[0]
    
    #loop through the controls list, parent them to the head control if they're not in the exclude list
    parent_object = 'head_joint_anim'
    exclude_objects = ['chin_joint_anim','head_joint_anim','mouth_bottom_middle_joint_anim','mouth_bottom_side_joint_R_anim','mouth_bottom_side_joint_L_anim','mouth_bottom_tip_joint_R_anim','mouth_bottom_tip_joint_L_anim','mouth_inside_joint_4_anim','mouth_inside_joint_5_anim','mouth_inside_joint_6_anim','mouth_inside_joint_9_anim','mouth_inside_joint_10_anim','mouth_top_middle_joint_anim','mouth_top_middle_joint_anim','mouth_top_side_joint_R_anim','mouth_top_side_joint_L_anim','mouth_top_tip_joint_R_anim','mouth_top_tip_joint_L_anim']
    for i in face_controls_list:
        if i not in exclude_objects:
            cmds.parent(i, parent_object)
    
    #parent the excluded controls
    parent_them('chin_joint_anim','jaw_joint_anim')

    parent_them('mouth_top_middle_joint_anim','mouth_inside_joint_1_anim')
    parent_them('mouth_top_side_joint_R_anim','mouth_inside_joint_7_anim')
    parent_them('mouth_top_side_joint_L_anim','mouth_inside_joint_2_anim')
    parent_them('mouth_top_tip_joint_R_anim','mouth_inside_joint_8_anim')
    parent_them('mouth_top_tip_joint_L_anim','mouth_inside_joint_3_anim')
    parent_them('mouth_bottom_tip_joint_L_anim','mouth_inside_joint_6_anim')
    parent_them('mouth_bottom_tip_joint_R_anim','mouth_inside_joint_10_anim')
    parent_them('mouth_bottom_side_joint_L_anim','mouth_inside_joint_5_anim')
    parent_them('mouth_bottom_side_joint_R_anim','mouth_inside_joint_9_anim')
    parent_them('mouth_bottom_middle_joint_anim','mouth_inside_joint_4_anim')
    
    parent_them('eyebrow_01_joint_L_anim','eyebrow_whole_anim_L')
    parent_them('eyebrow_02_joint_L_anim','eyebrow_whole_anim_L')
    parent_them('eyebrow_03_joint_L_anim','eyebrow_whole_anim_L')
    parent_them('eyebrow_01_joint_R_anim','eyebrow_whole_anim_R')
    parent_them('eyebrow_02_joint_R_anim','eyebrow_whole_anim_R')
    parent_them('eyebrow_03_joint_R_anim','eyebrow_whole_anim_R')
    parent_them('mouth_inside_joint_1_anim','mouth_whole_anim')
    parent_them('mouth_inside_joint_2_anim','mouth_whole_anim')
    parent_them('mouth_inside_joint_3_anim','mouth_whole_anim')
    parent_them('mouth_inside_joint_4_anim','mouth_whole_anim')
    parent_them('mouth_inside_joint_5_anim','mouth_whole_anim')
    parent_them('mouth_inside_joint_6_anim','mouth_whole_anim')
    parent_them('mouth_inside_joint_7_anim','mouth_whole_anim')
    parent_them('mouth_inside_joint_8_anim','mouth_whole_anim')
    parent_them('mouth_inside_joint_9_anim','mouth_whole_anim')
    parent_them('mouth_inside_joint_10_anim','mouth_whole_anim')
    
    parent_them('mouth_inside_joint_4_anim','jaw_joint_anim')
    parent_them('mouth_inside_joint_5_anim','jaw_joint_anim')
    parent_them('mouth_inside_joint_6_anim','jaw_joint_anim')
    parent_them('mouth_inside_joint_9_anim','jaw_joint_anim')
    parent_them('mouth_inside_joint_10_anim','jaw_joint_anim')
    
    parent_them('mouth_whole_anim','head_joint_anim')
    parent_them('eyebrow_whole_anim_L','head_joint_anim')
    parent_them('eyebrow_whole_anim_R','head_joint_anim')
    parent_them('eyes_control','head_joint_anim')
    
def parent_them(child_object,parent_object):
    cmds.parent(child_object, parent_object)
    
def parent_constraint_them(parent_object,child_object):
    cmds.parentConstraint(child_object, parent_object,maintainOffset=True)
         
def measure_joint_distance(joint_01, joint_02):
    '''using the two ear joints and the distance between them, the diameter of a nurbs circle is calculated
    then divided by 12, making the face 12 circles wide. This gives a unique circle diameter
    '''
    joint1_pos = cmds.xform('ear_joint_R', q=True, t=True, ws=True)
    joint2_pos = cmds.xform('ear_joint_L', q=True, t=True, ws=True) 
    # Calculate the distance between the two joints using the Pythagorean theorem
    distance = math.sqrt((joint2_pos[0] - joint1_pos[0])**2 + (joint2_pos[1] - joint1_pos[1])**2 + (joint2_pos[2] - joint1_pos[2])**2)
  
    circle_diameter = distance/12
    return circle_diameter
    
def calculate_mesh_width(mesh_name):
    ''' Get the bounding box of the mesh and calculate its width
    '''
    bbox = cmds.exactWorldBoundingBox(mesh_name)
    width = bbox[3] - bbox[0]
    joint_size=4*(width/21)
    
    return joint_size
    
def colour_red(anim_control):
    # Set the override color to red
    cmds.setAttr(anim_control + '.overrideEnabled', 1)
    cmds.setAttr(anim_control + '.overrideRGBColors', 1)
    cmds.setAttr(anim_control + '.overrideColorRGB', 1, 0, 0)
    
def colour_blue(anim_control):
    # Set the override color to blue 
    cmds.setAttr(anim_control + '.overrideEnabled', 1)
    cmds.setAttr(anim_control + '.overrideRGBColors', 1)
    cmds.setAttr(anim_control + '.overrideColorRGB', 0, 0, 1)
    
def colour_yellow(anim_control):
    # Set the override color to yellow
    cmds.setAttr(anim_control + '.overrideEnabled', 1)
    cmds.setAttr(anim_control + '.overrideRGBColors', 1)
    cmds.setAttr(anim_control + '.overrideColorRGB', 1, 1, 0)
    
def colour_green(anim_control):
    # Set the override color to green
    cmds.setAttr(anim_control + '.overrideEnabled', 1)
    cmds.setAttr(anim_control + '.overrideRGBColors', 1)
    cmds.setAttr(anim_control + '.overrideColorRGB', 0, 1, 0)
    
def clean_up(*args):
    '''Create a new display layer and clean up scene
    '''
    cmds.select(clear=True)
    layer_name = "joints"
    layer = cmds.createDisplayLayer(name=layer_name, noRecurse=True)
    joints = cmds.ls(type="joint")
    cmds.editDisplayLayerMembers(layer, joints)
    cmds.setAttr(layer + ".visibility", False)
    
def scale_rig_setup(*args):
    ''''Make the head uniformly scalable
    Create the Head_All_Grp group
    '''
    head_all_grp = cmds.group(empty=True, name='Head_All_Grp')
    rig_grp = cmds.group(empty=True, name='Rig_Grp')
    cmds.parent('head_joint', rig_grp)
    cmds.parent(rig_grp, head_all_grp)
    cmds.parent('head_joint_anim', head_all_grp)
    cmds.select('head_joint_anim', replace=True)
    cmds.select(rig_grp, add=True)
    cmds.scaleConstraint(weight=1)
    cmds.select(clear=True)

def create_ui():
    '''Create the UI 
    '''
    window = cmds.window(title="Auto Face Rigger", widthHeight=(670, 425))
    
    ######    CHANGE THIS LINE TO YOUR OWN DIRECTORY WITH THE IMAGES     ########
    image_path="C:\\Users\\Asuch\\Desktop"

    # Create a tab layout
    tab_layout = cmds.tabLayout("myTabLayout", parent=window)

    # Create the first tab, set the parent to the tab layout
    tab1 = cmds.rowColumnLayout("Face Rigging",numberOfColumns=2, parent=tab_layout)
    
    image_layout = cmds.image(image=image_path + '\\joint_placement_guide.png', parent = tab1)
    
    left_layout=cmds.columnLayout(adjustableColumn=True,parent=tab1)
    # Create a row column layout to split the tab into two sections
    split_layout = cmds.rowColumnLayout(numberOfColumns=5, parent=left_layout)
    
    # Add buttons to the left section of the split layout
    # Add empty text labeles as spacers
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.button(label='Add Face Selection',command=add_face_selection,bgc=(0.63,0.92,0.61),width=165)
    cmds.text(label="", width=10, height=10)
    cmds.button(label='Clear Face Selections', command=clear_face_selections,bgc=(0.97,0.96,0.75),width=165)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.button(label='Generate Face Joints', command=create_joints)
    cmds.text(label="", width=10, height=10)
    cmds.button(label='Create Head and Jaw Joints', command=create_head_joint)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.button(label='Mirror Joints', command=mirror_joints)
    cmds.text(label="", width=10, height=10)
    cmds.button(label='Create Controls', command=create_controls)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="", width=10, height=10)
    
    section2_layout = cmds.columnLayout(parent=left_layout)
    cmds.text(label="", width=10, height=10)
    cmds.text(label="Instructions", width=310, height=10,font='boldLabelFont')
    cmds.text(label="", width=10, height=10)
    
    cmds.text(label="1) Make sure the head, left eye, right eye, are separate objects")
    cmds.text(label="", width=10, height=5)
    cmds.text(label="2) Rename head mesh to 'Head', left eye to 'Left_eye', right eye to 'Right_eye'")
    cmds.text(label="", width=10, height=5)
    cmds.text(label="3) The image to the left illustrates the order and position of faces to be")
    cmds.text(label="   selected. Follow this order and position, each time you select a face click the")
    cmds.text(label="   'add f ace selection' button. Do not shift select multiple faces, repeat the")
    cmds.text(label="   porocess one face at a time.")
    cmds.text(label="", width=10, height=5)
    cmds.text(label="4) Click 'Generate Face Joints' button. The joints will be placed and resized")
    cmds.text(label="", width=10, height=5)
    cmds.text(label="5) Click 'Create Head and Jaw Joints' button. Joints will be parented")
    cmds.text(label="", width=10, height=5)
    cmds.text(label="6) Click 'Mirror Joints' button. Joints will be mirrored and renamed")
    cmds.text(label="", width=10, height=5)
    cmds.text(label="7) Click 'Create Controls' button. The controls will be placed and resized ")

    cmds.setParent(tab1)
    cmds.setParent("..")
    cmds.setParent("..")

    # Create the second tab, set the parent to the tab layout
    tab2 = cmds.rowColumnLayout("Face Skinning", parent=tab_layout)
    cmds.setParent("..")

    cmds.text(label="", width=10, height=10,parent=tab2)
    cmds.text(label="Bonus feature. This skins the joints very roughly, Fine tune the weights in the weight paint editor", width=700, height=20,parent=tab2)
    cmds.text(label="", width=10, height=10,parent=tab2)
    cmds.button(label='Auto Skin Joints', command=auto_skin, parent=tab2, width=100)
    cmds.text(label="", width=10, height=10,parent=tab2)
    cmds.text(label="Add uniform rig scaling to the head_joint_anim", width=500, height=20,parent=tab2)
    cmds.text(label="", width=10, height=10,parent=tab2)
    cmds.button(label='Make Scalable', command=scale_rig_setup, parent=tab2, width=100)
    cmds.text(label="", width=10, height=10,parent=tab2)
    image_layout = cmds.image(image=image_path + '\\Skinning_img.png', parent = tab2)

    # Show the window
    cmds.showWindow(window)

create_ui()

####References#####

#The model in the Face Rigging image by: MKULTRA, March, 2023, ava;iable on: https://sketchfab.com/3d-models/realistic-young-girl-head-lowpoly-basemesh-a576ffbaea4743b4bf367a8c4107cc16
#The model in the Face Skinning image by: Dance M, June, 2007, avaliable on: https://www.turbosquid.com/3d-models/3dsmax-cartoon-head/356688