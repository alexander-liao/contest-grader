# ignore first line
gets
scores = gets.chomp.split(' ').map{ |s| s.to_i }
keenanScore = gets.to_i
scores << keenanScore
mood = (scores.sort.reverse.index(keenanScore) <= 19 ? "happy!" : "sad.")
puts "Keenan is #{mood}"