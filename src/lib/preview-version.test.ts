import { describe, expect, it } from 'vitest';
import { articlePreviewVersion, projectPreviewVersion } from './preview-version';

describe('Studio preview versions', () => {
  it('matches the Python article fingerprint', () => {
    expect(articlePreviewVersion({ title:'棱镜',description:'清晰',category:'写作',tags:['A','中文'],collection:null,collectionOrder:null,featured:true,draft:false,canonical:null },'正文\r\n'))
      .toBe('246cddcc998b9d18ebd1257199f576779ddd11f39a957af0c3578b7f57c4a72e');
  });
  it('matches the Python project fingerprint', () => {
    expect(projectPreviewVersion({ repo:'o/r',title:'工具',description:'说明',topics:['cli','mac'],homepage:null,cover:null,coverAlt:null,featured:false,order:2 }))
      .toBe('6d6f99f07afa98739f4307b830b10663d9c5d75eb99aa562913b08cc4d736482');
  });
});
