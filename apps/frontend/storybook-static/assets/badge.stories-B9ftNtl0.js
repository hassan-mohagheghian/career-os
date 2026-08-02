import{i as e}from"./preload-helper-MclHqJXp.js";import{_ as t}from"./iframe-Bob7LAsN.js";import{n,t as r}from"./utils-vOBo-Xqw.js";import{n as i,t as a}from"./dist-lsPhnvH5.js";function o({className:e,variant:t,...n}){return(0,s.jsx)(`div`,{className:r(c({variant:t}),e),...n})}var s,c,l=e((()=>{s=t(),i(),n(),c=a(`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2`,{variants:{variant:{default:`border-transparent bg-primary text-primary-foreground hover:bg-primary/80`,secondary:`border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80`,destructive:`border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80`,outline:`text-foreground`}},defaultVariants:{variant:`default`}}),o.__docgenInfo={description:``,methods:[],displayName:`Badge`,props:{variant:{required:!1,tsType:{name:`union`,raw:`"default" | "secondary" | "destructive" | "outline"`,elements:[{name:`literal`,value:`"default"`},{name:`literal`,value:`"secondary"`},{name:`literal`,value:`"destructive"`},{name:`literal`,value:`"outline"`}]},description:``}}}})),u,d,f,p,m,h,g,_;e((()=>{u=t(),l(),d={title:`shared/ui/Badge`,component:o,tags:[`autodocs`],argTypes:{variant:{control:`select`,options:[`default`,`secondary`,`destructive`,`outline`]}}},f={args:{children:`Badge`,variant:`default`}},p={args:{children:`Secondary`,variant:`secondary`}},m={args:{children:`Destructive`,variant:`destructive`}},h={args:{children:`Outline`,variant:`outline`}},g={render:()=>(0,u.jsxs)(`div`,{className:`flex gap-2`,children:[(0,u.jsx)(o,{variant:`default`,children:`Active`}),(0,u.jsx)(o,{variant:`secondary`,children:`Draft`}),(0,u.jsx)(o,{variant:`destructive`,children:`Expired`}),(0,u.jsx)(o,{variant:`outline`,children:`Archived`})]})},f.parameters={...f.parameters,docs:{...f.parameters?.docs,source:{originalSource:`{
  args: {
    children: 'Badge',
    variant: 'default'
  }
}`,...f.parameters?.docs?.source}}},p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
  args: {
    children: 'Secondary',
    variant: 'secondary'
  }
}`,...p.parameters?.docs?.source}}},m.parameters={...m.parameters,docs:{...m.parameters?.docs,source:{originalSource:`{
  args: {
    children: 'Destructive',
    variant: 'destructive'
  }
}`,...m.parameters?.docs?.source}}},h.parameters={...h.parameters,docs:{...h.parameters?.docs,source:{originalSource:`{
  args: {
    children: 'Outline',
    variant: 'outline'
  }
}`,...h.parameters?.docs?.source}}},g.parameters={...g.parameters,docs:{...g.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex gap-2">
      <Badge variant="default">Active</Badge>
      <Badge variant="secondary">Draft</Badge>
      <Badge variant="destructive">Expired</Badge>
      <Badge variant="outline">Archived</Badge>
    </div>
}`,...g.parameters?.docs?.source}}},_=[`Default`,`Secondary`,`Destructive`,`Outline`,`StatusExample`]}))();export{f as Default,m as Destructive,h as Outline,p as Secondary,g as StatusExample,_ as __namedExportsOrder,d as default};