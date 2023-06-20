# TypeQL generator for LinkML

A [TypeQL](https://github.com/vaticle/typeql) generator for the [LinkML](https://github.com/linkml/linkml) open data
modeling language, allowing conversion of LinkML schemas and data into TypeQL queries and vice-versa. Intended to be a
general system of conversion, development will first focus on building the
[Biolink Model](https://github.com/biolink/biolink-model).

## Data model equivalence

| Biolink     | LinkML | TypeQL    | Comments                                                                                                                                                                                        |
|-------------|--------|-----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Named thing | Class  | Entity    |                                                                                                                                                                                                 |
| Association | Class  | Relation  |                                                                                                                                                                                                 |
|             | Class  | Attribute | As attributes are first-class citizens in TypeQL, it is necessary to model them as classes in LinkML.                                                                                           |
| Type        | Type   | Data type | LinkML has basic and complex data types. Data types in TypeQL would be the attribute value types: long, double, string, boolean, and datetime. Lists in LinkML would be split using delimiters. |
| Slot        | Slot   | Edge      | Slots can be used to model `role` edges (between relations and roleplayers), `has` edges (between attributes and owners), and `value` edges (between attributes and data types).                |
| Mixin       | Mixin  |           | TypeQL does not support multiple inheritance. Conversion would be unidirectional from Biolink to TypeQL.                                                                                        |
| Range       | Range  |           |                                                                                                                                                                                                 |
| Subset      | Subset |           |                                                                                                                                                                                                 |
| Enum        | Enum   |           |                                                                                                                                                                                                 |
