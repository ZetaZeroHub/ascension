from pathlib import Path
import json,hashlib,zipfile,shutil,subprocess
R=Path(__file__).resolve().parents[3];O=R/'outputs/Feisheng-MV/补充与舞蹈-v9'
observations={
'13':'手指逐渐握紧，裂缝亮度变化，单一道具保持；适合决心插镜。',
'14':'前脚靠近边缘并落稳，碎石下落，镜头连续。',
'15':'种子保持在地面，环状光向外扩散，适合核心触发之后。',
'16':'侧脸回望后微笑，面部与原角色大体一致，低分辨率微细节变化。',
'17':'侧步接抬臂和下蹲；主角与两位伴舞保持分离，手部微细节偏软。',
'18':'下蹲接前倾伸展；背景光带扩张较明显，可作强节拍视觉变化。',
'19':'侧向行进接抬臂舒展；背景雕塑在运镜中有轻微形状变化，宜短截使用。',
'20':'俯拍旋转及衣摆展开，主角与伴舞分离；实际转身幅度大于提示词设定。',
'21':'胸肩与手臂舞句，包含抬膝，手臂短暂遮挡脸部；近景细节偏软。',
'22':'背面迈步接转身收束，后排伴舞抬臂；实际转身大于提示词的四分之一圈。'}
review={'method':'full-file decoding plus sequential contact-sheet visual review; not real-time playback or frame-by-frame full-resolution review','sample_stride_frames':{'13':12,'14':12,'15':12,'16':8,'17':8,'18':8,'19':8,'20':8,'21':6,'22':6},'result':'usable editable footage with limitations documented','confidence':{'technical':'high','visual_microdetail':'medium'},'observations':observations}
(O/'审查/视觉检查.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
ids=['d6948561-6ab3-443d-a80a-20415428f005','3dfd0a00-97be-4775-896e-17d676e64929','003c6c25-0196-44b7-97a6-d1f153b72a61','f29d5085-2d11-467f-a53e-72d73c3a969a','932da5fb-9297-4221-be13-6ca73485fbac','972a1f33-32c0-4c68-b9d6-80e9876838b2','a8b6f914-dd3a-4e3f-9b8c-b21c940a308a','548e250f-058e-48db-a853-52a308c13464','18f26ad7-bc8c-46a0-af57-87076009370e','bf2d85a7-3d7e-41ad-bbf3-44fd2af9af24']
briefs=['手持开裂金色种子的手部微距，酒红大衣、金手环、暖灰城市虚焦背景','断桥边缘两只黑靴低机位细节，碎石与深渊','核心表面单个开裂金色种子微距，同心环，无人物','恢复城市中的主角后侧回望半身','黑棚正面全身，主角与两位灰色雕塑服装伴舞，白色残躯雕塑及苔藓景观','低机位三分之四全身独舞，白色羽翼雕塑及黑砾石枯草景观','侧面全身，三人舞，白色螺旋雕塑及枯山水盆景','高位俯拍三人舞，白色环状雕塑与圆形沙庭','三分之四半身近景，白雕塑虚焦与冷青横向光线','后方三分之四全身，白色胸像序列、树形苔藓岛与两位伴舞']
assets=[]
for n,sid in enumerate(range(13,23)):
    p=O/'frames'/f'{sid}.png'
    assets.append({'shot':str(sid),'provider':'built-in image_gen.imagegen','source_file':f'<USER_HOME>/.codex/generated_images/01a10d13-8b77-7111-b165-05f37f961a99/exec-{ids[n]}.png','saved_file':f'frames/{sid}.png','sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'creative_prompt_summary':briefs[n],'identity_reference':'reference/character.png','style':'warm grey B' if sid<17 else 'black studio, cold cyan-grey shadows, neutral skin, burgundy matte costume, white sculptures, restrained warm rim and horizontal optical streaks'})
(O/'首帧生成记录.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2),encoding='utf-8')
(O/'reference').mkdir(exist_ok=True);shutil.copy2(R/'outputs/Feisheng-MV/独立分镜-v6/reference/character.png',O/'reference/character.png')
manifest=json.loads((O/'素材清单.json').read_text(encoding='utf-8'))
concat=R/'work/feisheng/fast-v9/dance-concat.txt'
concat.write_text('\n'.join("file '"+str((O/x['file']).resolve()).replace('\\','/')+"'" for x in manifest if int(x['shot'])>=17),encoding='utf-8')
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(O/'舞蹈6镜头连续预览.mp4')],check=True)
archive=O.parent/'飞升-10段补充与舞蹈素材.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
    for p in sorted(O.rglob('*')):
        if p.is_file() and 'clips' not in p.relative_to(O).parts:z.write(p,Path(O.name)/p.relative_to(O))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    n=len(z.namelist())
print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'entries':n,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()},ensure_ascii=False))
