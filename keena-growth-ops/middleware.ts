import {NextResponse,type NextRequest} from 'next/server';
import {accessAllowed} from './lib/auth';
export async function middleware(request:NextRequest){
  if(await accessAllowed(request))return NextResponse.next();
  if(!process.env.KEENA_ACCESS_KEY || process.env.KEENA_ACCESS_KEY.length<24)return new NextResponse('Configure private pilot access before starting.',{status:503});
  return new NextResponse('Private Keena pilot',{status:401,headers:{'WWW-Authenticate':'Basic realm="Keena pilot", charset="UTF-8"','Cache-Control':'no-store'}});
}
export const config={matcher:['/((?!_next/static|_next/image|favicon.svg).*)']};
