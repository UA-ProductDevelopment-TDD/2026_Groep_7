# serial-protocol

| | |
|---|---|
| Link in de slides | https://docs.petoi.com/apis/serial-protocol |
| Opgehaald van | https://docs.petoi.com/apis/serial-protocol.md |
| Opgehaald op | 2026-10-06 |
| HTTP-status | 200 |
| Methode | GitBook-markdownexport (.md); GitBook-kop en -voettekst "Agent Instructions" weggelaten |

---

# Serial Protocol

We have defined a set of serial communication protocols for robots:&#x20;

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F8LVgTUXxZ23NFVti3Cre%2Fserial_commands.png?alt=media&amp;token=15e538ff-02ff-43fc-a31a-578c7e98704d" alt=""><figcaption></figcaption></figure>

All the tokens start with a single ASCII-encoded character to specify their parsing format. They are case-sensitive and usually in lowercase.&#x20;

{% hint style="info" %}
Some commands, like the **c** and **m** commands, can be combined.&#x20;

For example:

Successive "m8 40", "m8 -35", "m 0 50" can be written as "m8 40 8 -35 0 50".&#x20;

You can change the limit in the code, but there might be a systematic constraint for the serial buffer.
{% endhint %}

Try the following serial commands in [the serial monitor](https://docs.petoi.com/arduino-ide/serial-monitor):

* “**k**sit”
* “**m**0 30”
* “**m**0 -30”
* “**k**balance”
* “**k**wkF”
* “**k**trL”
* “**d**”

{% hint style="warning" %}
The quotation mark indicates that they are character strings. Don’t type quotation marks in the serial monitor.
{% endhint %}

You can refer to the macro definitions in OpenCat.h to utilize the most updated sets of tokens.&#x20;

{% @github-files/github-code-block url="<https://github.com/PetoiCamp/OpenCat/blob/3368dfd46d91cb453bb5fcca3ca4cf84712c922e/src/OpenCat.h#L204-L254>" %}

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FbSkyhmq6Tk0gkW51N309%2Ftokens.png?alt=media&amp;token=ea49b494-7623-43c9-aba4-2d7cadca6993" alt=""><figcaption></figcaption></figure>

Some more available commands for skills:

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F3XodRcaq7Wu56PS4YGYa%2FskillList.png?alt=media&amp;token=33409306-3e23-420c-bdf2-f28c6065129a" alt=""><figcaption></figcaption></figure>

The complete set of skills in effect is defined in [InstinctBittle.h](https://github.com/PetoiCamp/OpenCat/blob/main/src/InstinctBittle.h) or [InstinctNybble.h](https://github.com/PetoiCamp/OpenCat/blob/main/src/InstinctNybble.h):\
For example:

{% code overflow="wrap" %}

```cpp
const char* skillNameWithType[]={"bdFI","bkI","bkLI","crFI","crLI","hlwI","mhFI","mhLI","pcFI","phFI","phLI","trFI","trLI","vtFI","vtLI","wkFI","wkLI","balanceI","buttUpI","calibI","droppedI","liftedI","restI","sitI","strI","zeroN","bfI","ckI","climbCeilI","fdI","ffI","hiI","jyI","pdI","peeI","puI","pu1I","rcI","rlLI","rtI","stpI","tsI",};
```

{% endcode %}

All the skill names in the list can be called by adding a 'k' to the front and deleting the suffix. For example, there's "sitI" in the list. You can send "ksit" to call the sitting posture. If a skill has "F" or "L" as the second last character, it's a gait. It means walking forward or left. Walking right is a mirror of walking left. So you can send "kwkF", "kwkL", "kwkR" to make the robot walk. Similarly, there are other gaits like trot ("tr"), crawl ("cr"), and stepping ("vt").<br>
