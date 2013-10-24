#Colors
- primary: `#0cf`
- black: `#000`
- white: `#fff`

#Model Interactions
- Gif created: User += 1
- Gif deleted: User -= 2
- tag goes from unverified to verified: User += 1
    + if is not verified before and is verified after
- tag goes from verified to unverified: User -= 1
    + if tag is verified before and is not verified after
-tag goes from unverified to bad: User -= 1
    + if is not bad before and is bad now
- user stars Gif: Gif.stars += 1
- user unstars Gif: Gif.stars -= 1
- substitution proposal is accepted: User += 1

