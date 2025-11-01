/**
 * Preact + TypeScript popup source.
 * Uses chrome.storage to persist backend URL and current user across sessions.
 */
import { h, render } from 'preact';
import { useEffect, useState } from 'preact/hooks';

type User = { id: number; name: string } | null;

function useStored<T>(key: string, initial: T) {
  const [state, setState] = useState<T>(initial);
  useEffect(() => {
    chrome.storage.local.get([key], (res) => {
      if (res && res[key] !== undefined) setState(res[key]);
    });
  }, []);
  useEffect(() => {
    chrome.storage.local.set({ [key]: state });
  }, [state]);
  return [state, setState] as const;
}

function App() {
  const [backend, setBackend] = useStored<string>('backendUrl', 'http://localhost:8000');
  const [currentUser, setCurrentUser] = useStored<User>('currentUser', null);
  const [tmdbid, setTmdbid] = useState('');
  const [status, setStatus] = useState('');
  const [recs, setRecs] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);

  async function api(path: string, opts: any = {}) {
    const res = await fetch((backend || 'http://localhost:8000') + path, opts);
    if (!res.ok) throw new Error('API ' + res.status);
    return res.json();
  }

  async function createUser(name: string) {
    const u = await api('/users', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({name}) });
    setCurrentUser(u);
    setStatus('User set: ' + u.name);
  }

  async function addWatched() {
    if (!currentUser) return setStatus('Set user first');
    const id = parseInt(tmdbid || '0');
    try {
      const r = await api(`/users/${currentUser.id}/history`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({tmdb_id: id}) });
      setStatus('Added watched');
    } catch (e: any) { setStatus(String(e)); }
  }

  async function getRecs() {
    if (!currentUser) return setStatus('Set user first');
    try {
      const r = await api(`/users/${currentUser.id}/recommend`);
      setRecs(r);
      setStatus('Got ' + r.length + ' recs');
    } catch (e: any) { setStatus(String(e)); }
  }

  async function openDetails(tmdb_id: number) {
    try {
      const d = await api(`/movies/${tmdb_id}`);
      setSelected(d);
    } catch (e:any) { setStatus(String(e)); }
  }

  return (
    <div style={{width:320,padding:8,fontFamily:'Arial'}}>
      <h3>Flick Picker</h3>
      <div>
        <input placeholder="Your name" id="name" style={{width:'100%',padding:6}} />
        <button onClick={() => createUser((document.getElementById('name') as any).value)} style={{width:'100%',marginTop:6}}>Create / Set User</button>
      </div>
      <div style={{marginTop:8}}>
        <input placeholder="TMDB ID" value={tmdbid} onInput={(e:any)=>setTmdbid(e.target.value)} style={{width:'100%',padding:6}} />
        <button onClick={addWatched} style={{width:'100%',marginTop:6}}>Add Watched</button>
      </div>
      <div style={{marginTop:8}}>
        <button onClick={getRecs} style={{width:'100%'}}>Get Recommendations</button>
      </div>
      <div style={{marginTop:8,color:'green'}}>{status}</div>
      <div id="recs" style={{marginTop:8}}>
        {recs.length > 0 && (
          <div style={{display:'flex',flexDirection:'column',gap:8}}>
            {recs.map((r:any) => (
              <div key={r.tmdb_id} style={{display:'flex',alignItems:'center',gap:8,cursor:'pointer'}} onClick={() => openDetails(r.tmdb_id)}>
                <img src={(backend||'http://localhost:8000') + `/images/tmdb/${r.tmdb_id}/poster?size=w185`} onError={(e:any)=>{e.currentTarget.src = 'https://image.tmdb.org/t/p/w92'+(r.poster_path||'');}} alt={r.title} style={{width:48,height:72,objectFit:'cover',borderRadius:4}} />
                <div style={{flex:1}}>
                  <div style={{fontWeight:600}}>{r.title}</div>
                  <div style={{fontSize:12,color:'#666'}}>{r.score.toFixed(3)}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {selected && (
        <div style={{marginTop:10,padding:8,border:'1px solid #ddd',borderRadius:6,background:'#fff'}}>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
            <strong>{selected.title}</strong>
            <button onClick={() => setSelected(null)}>Close</button>
          </div>
          {selected.data && selected.data.backdrop_path && (
            <img src={(backend||'http://localhost:8000') + `/images/tmdb/${selected.tmdb_id}/backdrop?size=w780`} onError={(e:any)=>{e.currentTarget.src = 'https://image.tmdb.org/t/p/w780'+selected.data.backdrop_path;}} alt="backdrop" style={{width:'100%',borderRadius:6,marginTop:8}} />
          )}
          <div style={{marginTop:8}}>{selected.data?.overview}</div>
        </div>
      )}
    </div>
  );
}

const root = document.createElement('div');
document.body.appendChild(root);
render(<App />, root);
