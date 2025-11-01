import { h, render } from 'preact';
import { useEffect, useState } from 'preact/hooks';

function OptionsApp() {
  const [backend, setBackend] = useState('http://localhost:8000');
  const [userId, setUserId] = useState('');
  const [status, setStatus] = useState('');

  useEffect(()=>{
    chrome.storage.local.get(['backendUrl','currentUser'], (res:any)=>{
      if(res.backendUrl) setBackend(res.backendUrl);
      if(res.currentUser) setUserId(String(res.currentUser.id));
    })
  },[])

  function save(){
    const cu = userId ? { id: parseInt(userId) } : null;
    chrome.storage.local.set({ backendUrl: backend, currentUser: cu }, ()=>{
      setStatus('Saved');
    })
  }

  function clearAll(){
    chrome.storage.local.remove(['backendUrl','currentUser'], ()=>{ setStatus('Cleared'); setBackend(''); setUserId(''); })
  }

  return (
    <div style={{padding:12,fontFamily:'Arial'}}>
      <h3>Flick Picker Options</h3>
      <div>
        <label>Backend URL</label>
        <input value={backend} onInput={(e:any)=>setBackend(e.target.value)} style={{width:'100%'}} />
      </div>
      <div style={{marginTop:8}}>
        <label>Persisted User ID</label>
        <input value={userId} onInput={(e:any)=>setUserId(e.target.value)} style={{width:'100%'}} />
      </div>
      <div style={{marginTop:8}}>
        <button onClick={save}>Save</button>
        <button onClick={clearAll} style={{marginLeft:8}}>Clear</button>
      </div>
      <div style={{marginTop:8,color:'green'}}>{status}</div>
    </div>
  )
}

const root = document.createElement('div');
document.body.appendChild(root);
render(<OptionsApp />, root);
