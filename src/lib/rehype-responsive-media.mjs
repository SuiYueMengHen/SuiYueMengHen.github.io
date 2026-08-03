const textValue=(node)=>node?.type==='text'?node.value:'';

function mediaOptions(value='') {
  const match=value.match(/^\s*\{([^}]*)\}/s);
  if(!match)return {width:100,caption:'',consumed:0};
  const fields=match[1];
  const widthMatch=fields.match(/(?:^|\s)width\s*=\s*(\d{1,3})%?/i);
  const captionMatch=fields.match(/(?:^|\s)caption\s*=\s*("(?:\\.|[^"])*"|'(?:\\.|[^'])*'|“[^”]*”|‘[^’]*’)/is);
  const width=Math.max(10,Math.min(100,Number(widthMatch?.[1]||100)));
  let caption='';
  if(captionMatch){
    try{caption=captionMatch[1][0]==='"'?JSON.parse(captionMatch[1]):captionMatch[1].slice(1,-1).replace(/\\'/g,"'");}
    catch{caption=captionMatch[1].slice(1,-1);}
  }
  return {width,caption,consumed:match[0].length};
}

function imageOptions(image) {
  const title=String(image?.properties?.title||'');
  const match=title.match(/^prism:\s*width=(\d{1,3})%?(?:;\s*caption=(.*))?$/is);
  if(!match)return null;
  delete image.properties.title;
  return {width:Math.max(10,Math.min(100,Number(match[1]))),caption:(match[2]||'').trim(),consumed:0};
}

function figure(image,options,sourceProperties={}) {
  const img={...image,properties:{...(image.properties||{}),loading:'lazy',decoding:'async'}};
  const children=[img];
  if(options.caption)children.push({type:'element',tagName:'figcaption',properties:{},children:[{type:'text',value:options.caption}]});
  return {type:'element',tagName:'figure',properties:{...sourceProperties,className:['media-figure'],style:`--media-width:${options.width}%`},children};
}

function parseMediaParagraph(node) {
  if(node?.type!=='element'||node.tagName!=='p')return null;
  const items=[];let index=0;
  while(index<node.children.length){
    const child=node.children[index];
    if(child.type==='text'&&!child.value.trim()){index+=1;continue;}
    if(child.type!=='element'||child.tagName!=='img')return null;
    let options=imageOptions(child)||{width:100,caption:'',consumed:0};
    const next=node.children[index+1];
    if(next?.type==='text'){
      const trailing=mediaOptions(next.value);
      if(trailing.consumed){
        options=trailing;
        next.value=next.value.slice(options.consumed);
        if(next.value.trim())return null;
        index+=1;
      }
    }
    items.push(figure(child,options,node.properties));index+=1;
  }
  if(!items.length)return null;
  if(items.length===1)return items[0];
  return {type:'element',tagName:'div',properties:{...node.properties,className:['media-gallery']},children:items};
}

function plainText(node){return node?.children?.map(textValue).join('').trim()||'';}
function isMedia(node){return node?.type==='element'&&(node.tagName==='figure'||node.properties?.className?.includes('media-gallery'));}

function transformParent(parent) {
  if(!Array.isArray(parent?.children))return;
  parent.children.forEach(transformParent);
  parent.children=parent.children.map((child)=>parseMediaParagraph(child)||child);
  const output=[];
  for(let index=0;index<parent.children.length;index+=1){
    const child=parent.children[index];
    if(child?.tagName==='p'&&plainText(child)===':::gallery'){
      const collected=[];let cursor=index+1;
      while(cursor<parent.children.length&&plainText(parent.children[cursor])!==':::'){
        if(isMedia(parent.children[cursor]))collected.push(parent.children[cursor]);
        else if(plainText(parent.children[cursor]))break;
        cursor+=1;
      }
      if(collected.length&&cursor<parent.children.length&&plainText(parent.children[cursor])===':::'){
        const figures=collected.flatMap((item)=>item.tagName==='figure'?[item]:item.children);
        output.push({type:'element',tagName:'div',properties:{...(child.properties||{}),className:['media-gallery']},children:figures});
        index=cursor;continue;
      }
    }
    output.push(child);
  }
  parent.children=output;
}

/** Render Prism Notes image attributes and gallery fences as responsive figures. */
export function rehypeResponsiveMedia(){return (tree)=>transformParent(tree);}

export const responsiveMediaInternals={imageOptions,mediaOptions,parseMediaParagraph};
