function classes(node){
  const value=node?.properties?.className;
  return Array.isArray(value)?value:String(value||'').split(/\s+/);
}

function mathCode(node,kind){
  return node?.type==='element'&&classes(node).includes(`math-${kind}`);
}

function textValue(node){
  return (node?.children||[]).filter((child)=>child.type==='text').map((child)=>child.value).join('');
}

function transform(parent){
  if(!Array.isArray(parent?.children))return;
  parent.children=parent.children.map((node)=>{
    if(node?.type==='element'&&node.tagName==='pre'){
      const code=node.children?.find((child)=>mathCode(child,'display'));
      if(code){
        const source=textValue(code);
        return {type:'element',tagName:'div',properties:{...(node.properties||{}),className:['math-source','math-source--display']},children:[{type:'text',value:`\\[${source}\\]`}]};
      }
    }
    if(mathCode(node,'inline')){
      const source=textValue(node);
      return {type:'element',tagName:'span',properties:{...(node.properties||{}),className:['math-source','math-source--inline']},children:[{type:'text',value:`\\(${source}\\)`}]};
    }
    transform(node);return node;
  });
}

/** Keep TeX in the page so MathJax 4 can line-break against the live container width. */
export function rehypeClientMath(){return (tree)=>transform(tree);}

export const clientMathInternals={transform};
