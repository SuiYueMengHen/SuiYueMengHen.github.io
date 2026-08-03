function classes(node){const value=node?.properties?.className;return Array.isArray(value)?value:String(value||'').split(/\s+/);}
function textChild(node){return node?.children?.find((child)=>child.type==='text');}

function transform(parent){
  if(!Array.isArray(parent?.children))return;
  parent.children=parent.children.map((node)=>{
    if(node?.type==='element'&&classes(node).includes('math-display')){
      const text=textChild(node);const match=text?.value?.match(/\s*\\tag\{([^{}]*)\}\s*$/s);
      if(match){
        text.value=text.value.slice(0,match.index).trimEnd();
        return {type:'element',tagName:'div',properties:{...(node.properties||{}),className:['equation-shell']},children:[node,{type:'element',tagName:'span',properties:{className:['equation-tag'],'aria-label':`公式编号 ${match[1]}`},children:[{type:'text',value:`(${match[1]})`}]}]};
      }
    }
    transform(node);return node;
  });
}

/** Keep equation numbers outside MathJax SVG so they own a stable right column. */
export function rehypeEquationTags(){return (tree)=>transform(tree);}

export const equationTagInternals={transform};
