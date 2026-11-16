import base64,json,pathlib,shutil,subprocess,time,sys
queue=pathlib.Path('/Users/federico/Library/Containers/com.keevault.app.uitests.xctrunner/Data/tmp/KeeForgeNativeReviewCapture')
output=pathlib.Path('/Users/federico/work/active/open-source/KeeForge/scratch/pr-readiness/native-captures')
output.mkdir(exist_ok=True)
cli='/Applications/Orca.app/Contents/Resources/bin/orca'
seen=set(); expected=int(sys.argv[1]) if len(sys.argv)>1 else 5; deadline=time.monotonic()+600
while len(seen)<expected and time.monotonic()<deadline:
 request=queue/'request.json'
 if not request.exists(): time.sleep(.2);continue
 try: data=json.loads(request.read_text())
 except (OSError,json.JSONDecodeError): time.sleep(.2);continue
 name=data['name']
 if name in seen: time.sleep(.2);continue
 seen.add(name)
 try:
  pid=int(data['pid']);window=int(data['windowID'])
  binary=subprocess.check_output(['/bin/ps','-p',str(pid),'-o','comm='],text=True).strip()
  assert '/scratch/pr-readiness/dd-native-review/' in binary and binary.endswith('/KeeForge.app/Contents/MacOS/KeeForge'),binary
  def call(args):
   r=subprocess.run([cli,'computer',*args,'--json'],capture_output=True,text=True,timeout=20)
   v=json.loads(r.stdout)
   assert r.returncode==0 and v.get('ok'),v.get('error')
   return v['result']
  inventory=call(['list-windows','--app',f'pid:{pid}'])
  assert any(int(w['id'])==window for w in inventory['windows']),inventory
  state=call(['get-app-state','--app',f'pid:{pid}','--window-id',str(window)])
  (output/(name+'.json')).write_text(json.dumps(state,ensure_ascii=False,indent=2))
  shot=state['screenshot'];target=output/(name+'.png')
  if shot.get('path'):shutil.copy2(shot['path'],target)
  else:target.write_bytes(base64.b64decode(shot['data']))
  assert target.read_bytes().startswith(b'\x89PNG'), 'No PNG'
  shutil.copy2(target,queue/(name+'.png'))
  print('Captured',name,flush=True)
 except Exception as e:
  (output/(name+'.error.txt')).write_text(str(e));print('Capture failed',name,str(e),flush=True)
 (queue/(name+'.done')).write_text('done')
print('Sidecar finished:',len(seen),'captures',flush=True)
