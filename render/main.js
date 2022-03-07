import {solids, polyhedra, models} from './model.js';
import {loadObj, edgeList} from './loader.js';
import * as g from './render.js';
import lines_ from './lines-z.js';

const ww = 500, wh = 500;
const canvas = document.getElementById('canv');
const ctx = canvas.getContext('2d');
canvas.width = ww; canvas.height = wh;

let lines = lines_.lines
// console.log(lines)
let lines_v = []
let lines_e = []
let line_idx = 0
for(let el of lines){
	let e = []
	for(let vec of el){
		lines_v.push(vec)
		e.push(line_idx)
		line_idx++
	}
	lines_e.push(e)
}
for(let v of lines_v){
		v[0] *= 1.5
		v[1] *= 1.5
}

/*
let obj = loadObj(Object.values(polyhedra)[2], 1.4);
let obj_v = obj.vertices.v;
let obj_i = obj.indices.v;
obj_i = edgeList(obj_i);
console.log(obj_i.length);
*/

let obj_v = lines_v;
let obj_i = lines_e;


let mouse = {x:0,y:0};
canvas.onmousemove = (e)=>{
    mouse.x = (2.*e.clientX-ww)/wh;
    mouse.y = (2.*e.clientY-wh)/wh;
}
canvas.ontouchmove = (e)=>{
    mouse.x = (2.*e.touches[0].clientX-ww)/wh;
    mouse.y = (2.*e.touches[0].clientY-wh)/wh;
}

let rot = g.create_rot(.0, -0.03, -0.0);
// obj_v = g.mat_mul_4(obj_v, g.create_rot(0.2, -0.5, 0.7));
let translate = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[mouse.x,mouse.y,0,1]];
let proj = g.create_proj(.7, .4 , .2);
let colors = { bkgd: 'darkslateblue', fill: 'darkslateblue', stroke: 'black' };
let scene = g.create_canvas_scene(ctx, ww, wh, colors, obj_v, obj_i, null, translate, null, proj);

document.body.onkeydown = (e)=>{
    if(e.key === " ") scene.r_mat = scene.r_mat ? 0 : rot;
}

window.setInterval(()=>{
        translate[3][0] = mouse.x*3;
        translate[3][1] = mouse.y*3; 
        translate[3][2] = 1;  
        scene.v_mat = g.lookAt( [-mouse.x*5, -mouse.y*5, -1.], [0,0, .5], .0);
        g.canvasrender(scene, 0);
}, 30);