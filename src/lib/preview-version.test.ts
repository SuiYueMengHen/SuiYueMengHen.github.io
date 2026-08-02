import { describe, expect, it } from 'vitest';
import { articlePreviewVersion, projectPreviewVersion } from './preview-version';

describe('Studio preview versions', () => {
  it('matches the Python article fingerprint', () => {
    expect(articlePreviewVersion({ title:'棱镜',description:'清晰',category:'写作',tags:['A','中文'],collection:null,collectionOrder:null,featured:true,draft:false,canonical:null },'正文\r\n'))
      .toBe('6634a4746ee55afa94e4b6aa230dc0031a95e4cfd83b716b788352fba1b8e732');
  });
  it('refreshes the article fragment when a reading structure option changes', () => {
    const article = { title:'棱镜',description:'清晰',category:'写作',tags:['A'],draft:true };
    expect(articlePreviewVersion(article, '正文'))
      .not.toBe(articlePreviewVersion({ ...article, showContents:false }, '正文'));
  });
  it('matches the Python project fingerprint', () => {
    expect(projectPreviewVersion({ repo:'o/r',title:'工具',description:'说明',topics:['cli','mac'],homepage:null,cover:null,coverAlt:null,featured:false,order:2 }))
      .toBe('6d6f99f07afa98739f4307b830b10663d9c5d75eb99aa562913b08cc4d736482');
  });
});
