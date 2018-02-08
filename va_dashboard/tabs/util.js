import React, { Component } from 'react';
import { Table, Tr, Td } from 'reactable';
import { Button, DropdownButton, MenuItem } from 'react-bootstrap';

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
function getTableRows(columns, data) {
    return columns.map((col, index) => {
        return <Td key={col} column={col}>{data[index]}</Td>
    });
}
function getTableRowsWithAction(columns, data, btnText, btnVal, btnClick) {
    let rows = getTableRows(columns, data);
    rows.push(<Td key="Actions" column="Actions"><Button type="button" bsStyle='primary' onClick={btnClick} value={btnVal}>{btnText}</Button></Td>);
    return rows;
}
function getTableRowsWithActions(columns, data, actions, action, param) {
    let rows = getTableRows(columns, data);
    let items = actions.map(a => {
        return <MenuItem eventKey={a}>{a}</MenuItem>
    });
    rows.push((
        <Td key="Actions" column="Actions">
            <DropdownButton bsStyle='primary' title="Choose" onSelect={action.bind(null, param)}>{items}</DropdownButton>
        </Td>
        ));
    return rows;
}

module.exports = {
    getRandomColor,
    getRandomColors,
    getTableRows,
    getTableRowsWithAction,
    getTableRowsWithActions
}
