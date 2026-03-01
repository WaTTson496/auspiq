# 拡張ポイントの境界

AuspiQ には差し替えや追加がしやすい場所があります。facet data、weight data、prompt template、generation settings が extension point です。

ただし、どこまでが拡張で、どこからが破壊的変更かは明確に区別する必要があります。たとえば prompt template の差し替えは extension ですが、生成応答の JSON 契約を壊すなら downstream も壊れます。facet code の追加も extension ですが、既存 weight data や candidate map と整合しなければ実質的には破壊的です。

extension point を広く持つほど、暗黙契約も増えやすくなります。AuspiQ では「差し替え可能だから安全」ではなく、「差し替え可能だが契約を守る必要がある」と考える方が正確です。
