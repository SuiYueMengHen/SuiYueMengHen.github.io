const excluded=/\\begin\s*\{|\\\\|\\(?:matrix|cases|aligned|gathered|split)\b/;
const relationCommands=['\\Longleftrightarrow','\\Longrightarrow','\\Rightarrow','\\leftrightarrow','\\rightarrow','\\implies','\\iff','\\leqslant','\\geqslant','\\approx','\\equiv','\\leq','\\geq','\\sim','\\qquad','\\quad'];

function detachTag(value){
  const match=value.match(/\s*(\\tag\{[^{}]*\})\s*$/s);
  return match?{body:value.slice(0,match.index).trimEnd(),tag:match[1]}:{body:value.trim(),tag:''};
}

function breakCandidates(value){
  const points=[];let depth=0;
  for(let index=0;index<value.length;index+=1){
    const char=value[index];
    if(char==='{'&&value[index-1]!=='\\'){depth+=1;continue;}
    if(char==='}'&&value[index-1]!=='\\'){depth=Math.max(0,depth-1);continue;}
    if(depth!==0)continue;
    if('+=<>'.includes(char)&&value[index-1]!=='\\')points.push(index);
    else if(char==='-'&&value[index-1]!=='\\'&&index>0)points.push(index);
    else if(char==='\\'){
      const command=relationCommands.find((candidate)=>value.startsWith(candidate,index));
      if(command)points.push(index);
    }
    else if((char===','||char===';')&&index>0)points.push(index+1);
  }
  return [...new Set(points)].sort((a,b)=>a-b);
}

export function smartBreakMath(value,target=28) {
  if(excluded.test(value))return value;
  const {body,tag}=detachTag(value);
  if(body.length<Math.max(48,Math.floor(target*1.15)))return value;
  const candidates=breakCandidates(body);
  if(!candidates.length)return value;
  const parts=[];let start=0;
  while(body.length-start>target){
    const after=candidates.filter((position)=>position>start+Math.floor(target*.42));
    if(!after.length)break;
    const nearby=after.filter((position)=>position<=start+Math.floor(target*1.15));
    const split=(nearby.length?nearby:after).reduce((best,current)=>Math.abs(current-(start+target))<Math.abs(best-(start+target))?current:best);
    if(split>=body.length-8)break;
    parts.push(body.slice(start,split).trim());start=split;
  }
  parts.push(body.slice(start).trim());
  if(parts.length<2)return value;
  return `\\begin{aligned}\n&${parts.join(' \\\\\n&{}')}\n\\end{aligned}${tag}`;
}

export function remarkSmartMathBreaks(){
  return (tree)=>{
    const walk=(node)=>{if(node?.type==='math'&&typeof node.value==='string')node.value=smartBreakMath(node.value);for(const child of node?.children||[])walk(child);};
    walk(tree);
  };
}

export const smartMathInternals={breakCandidates,detachTag};
