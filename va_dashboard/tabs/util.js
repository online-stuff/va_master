import React, { Component } from 'react';
import { Table, Tr, Td } from 'reactable';
import { Button, DropdownButton, MenuItem, Modal } from 'react-bootstrap';

function getRandomColor() {
    var letters = '0123456789ABCDEF'.split('');
    var color = '#';
    for (var i = 0; i < 6; i++ ) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}
function getRandomColors(count) {
    var letters = '0123456789ABCDEF'.split('');
    var colors = [];
    for(var j = 0; j < count; j++){
        var color = '#';
        for (var i = 0; i < 6; i++ ) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        colors.push(color);
    }
    return colors;
}
function arr2str(arr) {
    return arr.join(', ').slice(0, -2);
}
function str2arr(str) {
    return str.join(', ');
}
function obj2str(obj, key){
    return obj[key];
}
function obj2arr(arr, key){
    return arr.map(obj => obj[key]);
}
function objArr2str(arr, key) {
    return arr2str(obj2arr(arr, key));
}
function getTableRow(columns, data) {
    return columns.map((col, index) => {
        return <Td key={col} column={col}>{data[index]}</Td>
    });
}
function getTableRowWithLink(columns, data, onClick, index) {
    let result = [<Td key={columns[0]} column={columns[0]}><span className="link" onClick={onClick.bind(null, data[0], index)}>{data[0]}</span></Td>];
	return result.concat(getTableRow(columns.slice(1), data.slice(1)));
}
function getTableRowWithAction(columns, data, btnText, btnVal, btnClick, onLinkClick, rowIndex) {
    let rows = onLinkClick ? getTableRowWithLink(columns, data, onLinkClick, rowIndex) : getTableRow(columns, data);
    rows.push(<Td key="Actions" column="Actions"><Button type="button" bsStyle='primary' onClick={btnClick} value={btnVal}>{btnText}</Button></Td>);
    return rows;
}
function getTableRowWithActions(columns, data, actions, action, param, onLinkClick, rowIndex) {
    let rows = onLinkClick ? getTableRowWithLink(columns, data, onLinkClick, rowIndex) : getTableRow(columns, data);
    let items = actions.map(a => {
        return <MenuItem eventKey={a}>{a}</MenuItem>
    });
    rows.push((
        <Td key="Actions" column="Actions">
            <DropdownButton bsStyle='primary' title="Choose" onSelect={action.bind(null, param, rowIndex)}>{items}</DropdownButton>
        </Td>
        ));
    return rows;
}
function getModalHeader(title){
    return (
		<Modal.Header closeButton>
            <Modal.Title>{title}</Modal.Title>
		</Modal.Header>
    );
}
function getModalFooter(buttons){
    let btns = buttons.map(btn => {
        let { label, bsStyle, onClick } = btn;
        return <Button onClick={onClick} bsStyle={bsStyle}>{label}</Button>;
    });
	return (
		<Modal.Footer>
			{ btns }
		</Modal.Footer>
	);
}

function initializeFields(fields) {
    let state = {};
    for(let i=0; i<fields.length; i++)
        state[fields[i].key] = "";
    return state;
}

function initializeFieldsWithValues(fields, values) {
    let state = {}
    for(let i=0; i<fields.length; i++){
        let key = fields[i].key;
        state[key] = values[key];
    }
    return state;
}

module.exports = {
    getRandomColor,
    getRandomColors,
    getTableRow,
    getTableRowWithAction,
    getTableRowWithActions,
    getModalHeader,
	getModalFooter,
    initializeFields,
    initializeFieldsWithValues,
    arr2str,
    obj2arr,
    objArr2str
}
