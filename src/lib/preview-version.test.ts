import { describe, expect, it } from 'vitest';
import { articlePreviewVersion, categoryPreviewVersion, collectionPreviewVersion, projectPreviewVersion } from './preview-version';

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
  it('matches the Python collection fingerprint', () => {
    expect(collectionPreviewVersion({ title:'复分析',description:'简介',subtitle:'Complex',volume:'I',status:'ongoing',featured:false,order:1,cover:null,coverAlt:null }))
      .toBe('c0948ad0336293407cdaa703b42e719b34ccb52b3357436eb74c834652237cd6');
  });
  it('matches the Python category fingerprint', () => {
    expect(categoryPreviewVersion(['微积分','未分类','微积分'])).toBe('00fd32a60ab95d1a2edb4d9e6de773017ee1d7b1df07799015efec7ad26a9c77');
  });
});
