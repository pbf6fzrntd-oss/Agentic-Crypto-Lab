export async function accessAllowed(request:Request,key=process.env.KEENA_ACCESS_KEY,demo=process.env.KEENA_DEMO==='1'):Promise<boolean>{
  if(demo)return true;
  if(!key || key.length<24)return false;
  const header=request.headers.get('authorization')||'';if(!header.startsWith('Basic ')||header.length>1024)return false;
  let credentials;try{credentials=atob(header.slice(6));}catch{return false;}
  const expected='keena:'+key;
  const [a,b]=await Promise.all([credentials,expected].map(s=>crypto.subtle.digest('SHA-256',new TextEncoder().encode(s))));
  return new Uint8Array(a).reduce((diff,v,i)=>diff|(v^new Uint8Array(b)[i]),0)===0;
}
export function mutationAllowed(request:Request):boolean {
  const origin=request.headers.get('origin');
  return !!origin && origin===(process.env.KEENA_ORIGIN||new URL(request.url).origin);
}
