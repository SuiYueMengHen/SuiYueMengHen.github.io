function classes(node){const value=node?.properties?.className;return Array.isArray(value)?value:String(value||'').split(/\s+/);}
function textChild(node){return node?.children?.find((child)=>child.type==='text');}
function mathChild(node){
  if(node?.type==='element'&&classes(node).includes('math-display'))return node;
  if(node?.type==='element'&&node.tagName==='pre')return node.children?.find((child)=>child?.type==='element'&&classes(child).includes('math-display'));
}
function marker(tag){return {type:'element',tagName:'span',properties:{className:['equation-tag-marker'],'dataEquationTag':tag},children:[]};}

function extract(parent){
  if(!Array.isArray(parent?.children))return;
  const next=[];
  for(const node of parent.children){
    const math=mathChild(node);const text=textChild(math);
    if(text?.value)text.value=smartBreakMath(text.value);
    const match=text?.value?.match(/\s*\\tag\{([^{}]*)\}\s*$/s);
    if(match){
      text.value=text.value.slice(0,match.index).trimEnd();
      next.push(node,marker(match[1]));
    }else{extract(node);next.push(node);}
  }
  parent.children=next;
}

function isRenderedDisplay(node){return node?.type==='element'&&node.tagName==='mjx-container'&&String(node.properties?.display)==='true';}
function attach(parent){
  if(!Array.isArray(parent?.children))return;
  const next=[];
  for(let index=0;index<parent.children.length;index+=1){
    const node=parent.children[index];const following=parent.children[index+1];
    if(isRenderedDisplay(node)&&classes(following).includes('equation-tag-marker')){
      const tag=String(following.properties?.dataEquationTag||'');
      next.push({type:'element',tagName:'div',properties:{className:['equation-shell']},children:[node,{type:'element',tagName:'span',properties:{className:['equation-tag'],'aria-label':`公式编号 ${tag}`},children:[{type:'text',value:`(${tag})`}]}]});
      index+=1;
    }else{attach(node);next.push(node);}
  }
  parent.children=next;
}

/** Extract tags without disturbing the standard pre > code shape expected by MathJax. */
export function rehypeExtractEquationTags(){return (tree)=>extract(tree);}
/** Add the number only after MathJax has removed its temporary pre/code wrapper. */
export function rehypeAttachEquationTags(){return (tree)=>attach(tree);}

export const equationTagInternals={extract,attach};
import {smartBreakMath} from './remark-smart-math-breaks.mjs';
