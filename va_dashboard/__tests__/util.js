const util = require('../tabs/util');

test('empty object', () => {
    expect(util.isEmpty({})).toBe(true);
});

