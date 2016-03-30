    function shuffleArray(array) {
        array = array.slice();
        for (var i = array.length - 1; i > 0; i--) {
            var j = Math.floor(Math.random() * (i + 1));
            var temp = array[i];
            array[i] = array[j];
            array[j] = temp;
        }
        return array;
    }
var c = [1,2,3,4,5,6,7,8]
var incompleteMelodies = shuffleArray(c).slice(0, Math.round(Math.random() * (c.length - 1) + 1));
console.log(incompleteMelodies);
