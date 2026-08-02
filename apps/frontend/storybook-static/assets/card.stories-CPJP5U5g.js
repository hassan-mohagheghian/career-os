import{c as e,i as t}from"./preload-helper-MclHqJXp.js";import{U as n,_ as r}from"./iframe-Bob7LAsN.js";import{n as i,t as a}from"./utils-vOBo-Xqw.js";var o,s,c,l,u,d,f,p,m=t((()=>{o=r(),s=e(n(),1),i(),c=s.forwardRef(({className:e,...t},n)=>(0,o.jsx)(`div`,{ref:n,className:a(`rounded-lg border bg-card text-card-foreground shadow-sm`,e),...t})),c.displayName=`Card`,l=s.forwardRef(({className:e,...t},n)=>(0,o.jsx)(`div`,{ref:n,className:a(`flex flex-col space-y-1.5 p-6`,e),...t})),l.displayName=`CardHeader`,u=s.forwardRef(({className:e,...t},n)=>(0,o.jsx)(`h3`,{ref:n,className:a(`text-2xl font-semibold leading-none tracking-tight`,e),...t})),u.displayName=`CardTitle`,d=s.forwardRef(({className:e,...t},n)=>(0,o.jsx)(`p`,{ref:n,className:a(`text-sm text-muted-foreground`,e),...t})),d.displayName=`CardDescription`,f=s.forwardRef(({className:e,...t},n)=>(0,o.jsx)(`div`,{ref:n,className:a(`p-6 pt-0`,e),...t})),f.displayName=`CardContent`,p=s.forwardRef(({className:e,...t},n)=>(0,o.jsx)(`div`,{ref:n,className:a(`flex items-center p-6 pt-0`,e),...t})),p.displayName=`CardFooter`,c.__docgenInfo={description:``,methods:[],displayName:`Card`},l.__docgenInfo={description:``,methods:[],displayName:`CardHeader`},p.__docgenInfo={description:``,methods:[],displayName:`CardFooter`},u.__docgenInfo={description:``,methods:[],displayName:`CardTitle`},d.__docgenInfo={description:``,methods:[],displayName:`CardDescription`},f.__docgenInfo={description:``,methods:[],displayName:`CardContent`}})),h,g,_,v,y,b;t((()=>{h=r(),m(),g={title:`shared/ui/Card`,component:c,tags:[`autodocs`],render:e=>(0,h.jsxs)(c,{...e,children:[(0,h.jsxs)(l,{children:[(0,h.jsx)(u,{children:`Card Title`}),(0,h.jsx)(d,{children:`Card Description`})]}),(0,h.jsx)(f,{children:(0,h.jsx)(`p`,{children:`Card content goes here.`})}),(0,h.jsx)(p,{children:(0,h.jsx)(`p`,{children:`Card footer`})})]})},_={},v={render:()=>(0,h.jsx)(c,{children:(0,h.jsxs)(l,{children:[(0,h.jsx)(u,{children:`Header Only`}),(0,h.jsx)(d,{children:`Just the header section`})]})})},y={render:()=>(0,h.jsxs)(c,{className:`max-w-sm`,children:[(0,h.jsxs)(l,{children:[(0,h.jsx)(u,{children:`Job Position`}),(0,h.jsx)(d,{children:`Senior Software Engineer`})]}),(0,h.jsxs)(f,{children:[(0,h.jsx)(`p`,{children:`Berlin, Germany • Full-time • Visa sponsored`}),(0,h.jsx)(`p`,{className:`mt-2 text-sm text-muted-foreground`,children:`We are looking for an experienced software engineer to join our platform team.`})]}),(0,h.jsxs)(p,{className:`flex justify-between`,children:[(0,h.jsx)(`span`,{className:`text-sm text-muted-foreground`,children:`Posted 2 days ago`}),(0,h.jsx)(`span`,{className:`text-sm font-medium`,children:`Match: 85%`})]})]})},_.parameters={..._.parameters,docs:{..._.parameters?.docs,source:{originalSource:`{}`,..._.parameters?.docs?.source}}},v.parameters={...v.parameters,docs:{...v.parameters?.docs,source:{originalSource:`{
  render: () => <Card>
      <CardHeader>
        <CardTitle>Header Only</CardTitle>
        <CardDescription>Just the header section</CardDescription>
      </CardHeader>
    </Card>
}`,...v.parameters?.docs?.source}}},y.parameters={...y.parameters,docs:{...y.parameters?.docs,source:{originalSource:`{
  render: () => <Card className="max-w-sm">
      <CardHeader>
        <CardTitle>Job Position</CardTitle>
        <CardDescription>Senior Software Engineer</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Berlin, Germany • Full-time • Visa sponsored</p>
        <p className="mt-2 text-sm text-muted-foreground">
          We are looking for an experienced software engineer to join our platform team.
        </p>
      </CardContent>
      <CardFooter className="flex justify-between">
        <span className="text-sm text-muted-foreground">Posted 2 days ago</span>
        <span className="text-sm font-medium">Match: 85%</span>
      </CardFooter>
    </Card>
}`,...y.parameters?.docs?.source}}},b=[`Default`,`OnlyHeader`,`WithLongContent`]}))();export{_ as Default,v as OnlyHeader,y as WithLongContent,b as __namedExportsOrder,g as default};