/**
 * Preserve Markdown source ranges on rendered elements. Prism Studio uses
 * these markers to map an editor line to the matching rendered block.
 */
export function rehypeSourcePositions() {
  return (tree) => {
    const headingCounts=Array(7).fill(0);
    const walk = (node) => {
      if (node?.type === 'element' && node.position?.start?.line) {
        node.properties ||= {};
        node.properties['data-source-start'] = String(node.position.start.line);
        node.properties['data-source-end'] = String(node.position.end?.line ?? node.position.start.line);
        const match=/^h([1-6])$/.exec(node.tagName||'');
        if(match){
          const depth=Number(match[1]);
          for(let level=1;level<depth;level+=1)if(headingCounts[level]===0)headingCounts[level]=1;
          headingCounts[depth]+=1;
          for(let level=depth+1;level<=6;level+=1)headingCounts[level]=0;
          node.properties['data-heading-number']=depth===1?`${chineseSectionNumber(headingCounts[1])}、`:`§${headingCounts.slice(1,depth+1).join('.')}`;
        }
      }
      for (const child of node?.children ?? []) walk(child);
    };
    walk(tree);
  };
}

export function chineseSectionNumber(value) {
  const digits=['零','一','二','三','四','五','六','七','八','九'];
  if(!Number.isInteger(value)||value<=0)return String(value);
  if(value<10)return digits[value];
  if(value<20)return `十${value%10?digits[value%10]:''}`;
  if(value<100)return `${digits[Math.floor(value/10)]}十${value%10?digits[value%10]:''}`;
  return String(value);
}
