# joint-calibrator-bittle-x

| | |
|---|---|
| Link in de slides | https://docs.petoi.com/desktop-app/joint-calibrator/bittle-bittle-x |
| Opgehaald van | https://docs.petoi.com/desktop-app/joint-calibrator/bittle-bittle-x.md |
| Opgehaald op | 2026-10-06 |
| HTTP-status | 200 |
| Methode | GitBook-markdownexport (.md); GitBook-kop en -voettekst "Agent Instructions" weggelaten |

---

# Bittle / Bittle X

The subpages mention the joint calibration interface for Bittle / Bittle X in the Petoi Desktop App.

## Installation for the construction kit

After entering the calibration state, with all servos rotated to their zero angles, attach the head, and legs prepared in the previous section to the body. They are generally perpendicular to their linked body frames. The calibration pose is shown below:

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FMEoL83MnttMtpVZoBDaj%2Fimage.png?alt=media&amp;token=2fb18eb6-534b-4137-9fde-4555a1637a2b" alt=""><figcaption><p>Bittle's Calibration State</p></figcaption></figure>

Install the servo-related components according to the picture above and try to ensure that they are perpendicular to each other (the upper leg is perpendicular to the torso, and the lower leg is perpendicular to the upper leg).

### Install the head

In the calibration state, place the head as close to the central axis as possible and insert its servo shaft into the servo arm of the neck.

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FpMKiwLQSKNb7nbVbcQf4%2Fassets_bittle_cali_head01.jpeg?alt=media&amp;token=068c494a-073f-4c65-a780-cfce3e99c4b3" alt=""><figcaption></figcaption></figure>

Press down on the head so it is firmly attached to the neck.

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FghkDmfkN7FgFL2HAj3fF%2Fassets_bittle_cali_head02.jpeg?alt=media&amp;token=f69160ff-a83e-4889-ad40-42230ee58928" alt=""><figcaption></figcaption></figure>

### Install the legs&#x20;

Install upper leg and lower leg components to the output teeth of the servos after the Bittle is powered on and in the calibrated neutral position. Please keep the torso, upper leg, and lower leg installed vertically as much as possible, and do not install the lower leg backward, as shown in the picture.&#x20;

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F45sweR9hK7q0zQiddr0w%2Fassets_bittle_cali_leg01.jpeg?alt=media&amp;token=0598ffdf-0912-432b-a730-316ba0489038" alt=""><figcaption></figcaption></figure>

## Fine-tuning

{% hint style="info" %}
The **pre-assembled** robot should already have the components adequately installed. You can do the joint calibration for fine-tuning.&#x20;
{% endhint %}

Use the included L-shaped tool as a reference during calibration. According to the index numbers of the joints shown at the top of the interface (when calibrating the servos, adjust the upper leg first, then adjust the lower leg). Drag the corresponding slider (below the index number), or click the blank part of the slider track to fine-tune the joint to right angles.

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F9Cm2JDY0KfkYeNFRU3RC%2Fassets_bittle_-MSGw-I0q_j0kHosz8nz_-MSGx1sAobtzY1ucuddF_53.jpeg?alt=media\&token=9be5a3e5-6651-4f82-8599-9ea47e861fdc)

![Align the upper leg first](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FsStAdQLXoSDcLMiLlle0%2Fcalib1.png?alt=media\&token=7f499bec-e689-4cac-a736-d6d506e23b10)

![Pay attention to the reference edges for the lower leg](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F7VKzwUfx9XZBEltDnSsk%2Fcalib2.png?alt=media\&token=fa045175-f834-4bda-98dd-0dd174245539)

{% hint style="info" %}
If the offset is more than +/-9 degrees, you need to remove the corresponding leg and reinstall it by rotating one tooth and then dragging the corresponding slider. For example, when it is adjusted to +9 and still not right, remove the corresponding leg and shift one tooth when attaching it. Then, you should get a smaller offset in the opposite direction.&#x20;
{% endhint %}
